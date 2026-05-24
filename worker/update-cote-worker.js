/* Cloudflare Worker - declencheur du workflow + ajout de modeles personnalises.
 *
 * Deux endpoints exposes :
 *
 *   POST /             Relance le workflow "Mise a jour de la cote" (idem
 *                      bouton "Mettre a jour" du tableau de bord).
 *   POST /add-model    Ajoute un modele a data/custom-models.json puis lance
 *                      le workflow. Le scrape de ce modele intervient au
 *                      run qui suit (1-2 min).
 *
 * --- DEPLOIEMENT ---
 * 1. Jeton GitHub "fine-grained" (github.com/settings/tokens) :
 *      - Repository : mickcoco987/delsoltahiti
 *      - Permissions : Actions = Read and write, **Contents = Read and write**
 *        (la permission Contents est requise depuis l'ajout de /add-model :
 *         le Worker doit pouvoir editer data/custom-models.json).
 * 2. Deploie :
 *    a) Tableau de bord Cloudflare : Settings > Variables > secret
 *       GH_TOKEN = <le jeton>.
 *    b) wrangler : `wrangler deploy` puis `wrangler secret put GH_TOKEN`.
 * 3. Copie l'URL publique du Worker dans config.js (updateEndpoint).
 *
 * --- SECURITE ---
 * Endpoint public. /add-model accepte tout payload mais valide les champs
 * requis et les types. Cooldown 5min sur les triggers de workflow ; le
 * /add-model peut ecrire en plus du cooldown (l'edition est leger).
 */

const REPO = "mickcoco987/delsoltahiti";
const WORKFLOW = "update-cote.yml";
const REF = "main";
const COOLDOWN_MS = 5 * 60 * 1000;
const CUSTOM_MODELS_PATH = "data/custom-models.json";

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

    const url = new URL(request.url);
    if (url.pathname === "/add-model") {
      return await handleAddModel(request, env, cors);
    }
    return await handleTrigger(env, cors);
  },
};

async function handleTrigger(env, cors) {
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
    // Si le controle echoue, on laisse le declenchement tenter sa chance.
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
}

async function handleAddModel(request, env, cors) {
  let model;
  try {
    model = await request.json();
  } catch (err) {
    return reply({ ok: false, error: "JSON invalide." }, 400, cors);
  }

  const errors = validateModel(model);
  if (errors.length) {
    return reply({ ok: false, error: "Modèle invalide.", details: errors }, 400, cors);
  }

  // Lit le fichier existant (404 = on partira d'une liste vide).
  let existing = { models: [] };
  let sha = undefined;
  const getRes = await fetch(
    `https://api.github.com/repos/${REPO}/contents/${CUSTOM_MODELS_PATH}?ref=${REF}`,
    { headers: ghHeaders(env.GH_TOKEN) },
  );
  if (getRes.ok) {
    const data = await getRes.json();
    sha = data.sha;
    try {
      const decoded = atob(data.content.replace(/\n/g, ""));
      existing = JSON.parse(decoded);
      if (!existing.models) existing.models = [];
    } catch (err) {
      return reply({ ok: false, error: "custom-models.json existant illisible." }, 500, cors);
    }
  } else if (getRes.status !== 404) {
    return reply({ ok: false, error: "Lecture GitHub a échoué.", status: getRes.status }, 502, cors);
  }

  // Refuse les doublons de slug (built-in et custom).
  const reserved = ["ferrari-458", "ferrari-f8", "lamborghini-huracan", "porsche-911-gt3"];
  if (reserved.includes(model.slug)) {
    return reply({ ok: false, error: `Le slug "${model.slug}" est réservé.` }, 400, cors);
  }
  existing.models = existing.models.filter((m) => m.slug !== model.slug);
  existing.models.push(model);

  // Ecrit le fichier mis a jour.
  const payload = JSON.stringify(existing, null, 2) + "\n";
  const putRes = await fetch(
    `https://api.github.com/repos/${REPO}/contents/${CUSTOM_MODELS_PATH}`,
    {
      method: "PUT",
      headers: ghHeaders(env.GH_TOKEN),
      body: JSON.stringify({
        message: `feat: ajoute le modele personnalise '${model.slug}'`,
        content: btoa(unescape(encodeURIComponent(payload))),
        branch: REF,
        ...(sha ? { sha } : {}),
      }),
    },
  );
  if (!putRes.ok) {
    const text = await putRes.text();
    return reply(
      { ok: false, error: "Écriture GitHub a échoué.", status: putRes.status, detail: text.slice(0, 300) },
      502, cors,
    );
  }

  // Trigger le workflow (best-effort : on ne bloque pas sur un cooldown).
  await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: ghHeaders(env.GH_TOKEN),
      body: JSON.stringify({ ref: REF }),
    },
  ).catch(() => null);

  return reply({
    ok: true,
    message: `Modèle "${model.slug}" ajouté. Les données apparaîtront après le prochain scrape (~1-2 min).`,
    slug: model.slug,
  }, 200, cors);
}

function validateModel(m) {
  const errs = [];
  if (!m || typeof m !== "object") return ["payload doit être un objet JSON"];
  const req = ["slug", "brand", "name", "year_range", "price_range",
               "max_mileage", "variants"];
  for (const k of req) {
    if (m[k] === undefined || m[k] === null || m[k] === "") {
      errs.push(`champ requis manquant : ${k}`);
    }
  }
  if (m.slug && !/^[a-z0-9-]{3,40}$/.test(m.slug)) {
    errs.push("slug doit etre en kebab-case (a-z, 0-9, -), 3-40 caracteres");
  }
  if (m.year_range && (!Array.isArray(m.year_range) || m.year_range.length !== 2
      || m.year_range[0] >= m.year_range[1])) {
    errs.push("year_range doit etre [min, max] avec min < max");
  }
  if (m.price_range && (!Array.isArray(m.price_range) || m.price_range.length !== 2
      || m.price_range[0] >= m.price_range[1])) {
    errs.push("price_range doit etre [min, max] avec min < max");
  }
  if (m.variants && (!Array.isArray(m.variants) || m.variants.length === 0)) {
    errs.push("variants doit etre une liste non vide");
  }
  return errs;
}

function reply(body, status, cors) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...cors },
  });
}
