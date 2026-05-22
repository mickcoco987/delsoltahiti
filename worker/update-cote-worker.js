/* Cloudflare Worker - declencheur du workflow "Mise a jour de la cote 458".
 *
 * Permet au bouton du tableau de bord de lancer le workflow GitHub Actions
 * en un clic, sans exposer de jeton cote navigateur (le jeton vit ici, dans
 * un secret du Worker).
 *
 * --- DEPLOIEMENT ---
 * 1. Cree un jeton GitHub "fine-grained" : github.com/settings/tokens
 *      - Repository access : uniquement mickcoco987/delsoltahiti
 *      - Permissions : Actions = "Read and write"
 * 2. Deploie ce Worker, au choix :
 *    a) Tableau de bord Cloudflare : cree un Worker, colle ce fichier, puis
 *       Settings > Variables > ajoute un secret GH_TOKEN = <le jeton>.
 *    b) wrangler : `wrangler deploy` puis `wrangler secret put GH_TOKEN`.
 * 3. Copie l'URL publique du Worker dans config.js (champ updateEndpoint).
 *
 * --- SECURITE ---
 * L'endpoint est public ; il ne fait que relancer un scraper (action sans
 * risque). Un garde-fou refuse une relance si un run est deja en cours ou
 * date de moins de 5 minutes. Pour durcir, ajoute une regle de rate-limiting
 * Cloudflare ou Cloudflare Access.
 */

const REPO = "mickcoco987/delsoltahiti";
const WORKFLOW = "update-cote.yml";
const REF = "main";
const COOLDOWN_MS = 5 * 60 * 1000;

function ghHeaders(token) {
  return {
    "Authorization": `Bearer ${token}`,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "delsoltahiti-update-trigger",
  };
}

export default {
  async fetch(request, env) {
    const cors = {
      "Access-Control-Allow-Origin": env.ALLOW_ORIGIN || "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }
    if (request.method !== "POST") {
      return reply({ ok: false, error: "Méthode non autorisée." }, 405, cors);
    }
    if (!env.GH_TOKEN) {
      return reply({ ok: false, error: "GH_TOKEN non configuré." }, 500, cors);
    }

    // Garde-fou : pas de relance si un run est en cours ou tres recent.
    try {
      const runsRes = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=1`,
        { headers: ghHeaders(env.GH_TOKEN) },
      );
      if (runsRes.ok) {
        const last = (await runsRes.json()).workflow_runs?.[0];
        if (last && last.status !== "completed") {
          return reply({ ok: false, message: "Une mise à jour est déjà en cours." }, 200, cors);
        }
        if (last) {
          const age = Date.now() - new Date(last.updated_at).getTime();
          if (age < COOLDOWN_MS) {
            const mins = Math.ceil((COOLDOWN_MS - age) / 60000);
            return reply({ ok: false, message: `Mise à jour récente — réessaie dans ${mins} min.` }, 200, cors);
          }
        }
      }
    } catch (err) {
      // En cas d'echec du controle, on laisse le declenchement tenter sa chance.
    }

    const dispatch = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: ghHeaders(env.GH_TOKEN),
        body: JSON.stringify({ ref: REF }),
      },
    );

    if (dispatch.status === 204) {
      return reply({ ok: true, message: "Mise à jour lancée — données prêtes dans ~1-2 min." }, 200, cors);
    }
    return reply(
      { ok: false, error: "GitHub a refusé la demande.", status: dispatch.status },
      502, cors,
    );
  },
};

function reply(body, status, cors) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...cors },
  });
}
