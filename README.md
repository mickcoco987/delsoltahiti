# Cote supercars — marché US

Suivi de la **cote de plusieurs supercars** sur le marché des États-Unis :
un scraper automatisé collecte les annonces et un tableau de bord web affiche
l'évolution de la valeur. Au démarrage, l'utilisateur choisit la voiture à
suivre dans un sélecteur **marque → modèle**.

**Modèles suivis** : Ferrari 458, Ferrari F8, Lamborghini Huracán, Porsche 911
GT3. (Ajouter un modèle = ajouter une entrée dans `scraper/catalog.py`.)

## Aperçu

- **Sélecteur** (`index.html` + `app.js`) : écran d'accueil avec liste des
  marques et modèles disponibles. La sélection est persistée dans
  `localStorage`. Bouton **« ← Changer de voiture »** dans l'en-tête pour
  revenir au sélecteur.
- **Tableau de bord** (par modèle) : section **bonnes affaires**, indicateurs
  de cote, évolution dans le temps, prix par millésime, prix vs kilométrage et
  liste des annonces. 100 % HTML/CSS/JS, graphiques en SVG, sans dépendance.
- **Catalogue** (`scraper/catalog.py`) : source de vérité — chaque modèle y
  déclare ses bornes (millésimes, prix, kilométrage), ses versions, la règle
  de classification et les requêtes à passer à chaque source.
- **Scraper** (`scraper/`) : outil Python (bibliothèque standard uniquement,
  aucune installation requise) qui agrège les annonces de plusieurs sources
  (classic.com, API Marketcheck, eBay Motors) et tient à jour un historique
  de cote, par modèle.
- **Moteur de valeur** (`scraper/valuation.py`) : régression log-linéaire
  robuste, ajustée séparément pour chaque modèle.
- **Données** (`data/`) : un fichier `catalog.js` à la racine + un dossier
  par modèle (`data/<slug>/{listings,history,dashboard}.json|.js`), tous
  régénérés par le scraper.

## Démarrage rapide

```sh
# 1. Amorcer les données Ferrari 458 (échantillon de marché curé)
python3 -m scraper --seed

# 2. Servir le tableau de bord
python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

## Le scraper

```sh
# Un modèle, toutes les sources (par défaut --model ferrari-458)
python3 -m scraper --model ferrari-458 --source all

# Tous les modèles du catalogue, en une commande
python3 -m scraper --model all --source all --replace

# Une seule source (clé requise pour les APIs)
python3 -m scraper --model lamborghini-huracan --source marketcheck

# Réinitialise Ferrari 458 depuis l'échantillon curé
python3 -m scraper --seed
```

À chaque exécution, le scraper agrège les annonces du modèle ciblé, **estime
la valeur de marché de chacune** et détecte les bonnes affaires, recalcule
les statistiques (moyenne, médiane, fourchette, par version, par millésime)
et ajoute un point daté à l'historique de cote du modèle. Le bundle
`data/<slug>/dashboard.js` et le catalogue `data/catalog.js` (état de tous
les modèles) sont régénérés à chaque run.

### Sources de données

| Source        | Type    | Canal | Description                                          |
|---------------|---------|-------|------------------------------------------------------|
| `classic`     | scrape  | dealer | classic.com — agrégateur de cote du marché US.      |
| `marketcheck` | **API** | dealer | Marketcheck — inventaire US (clé requise).         |
| `ebay`        | **API** | auction | eBay Motors Browse API — enchères + Buy-It-Now.   |
| `dupont`      | scrape  | auction | DuPont Registry Live — enchères live US (best-effort). |
| `sothebys`    | scrape  | auction | RM Sotheby's — résultats d'enchères collectionneurs (best-effort). |
| `all`         | —       | —     | Enchaîne toutes les sources live ci-dessus (défaut). |
| `sample`      | local   | dealer | Relevés de marché curés (échantillon de démarrage). |

Chaque annonce porte un champ `kind` (`dealer` / `auction`). Le tableau de bord
sépare les deux dans deux **onglets** distincts.

Les sources `classic` et `bat` partagent la base `HtmlJsonSource` : elle
extrait le JSON embarqué des pages (JSON-LD, données Next.js…) et le parcourt
récursivement, ce qui la rend résistante aux changements de mise en page.

**Limite du scraping** : les sites d'annonces appliquent des protections
anti-bot. Si une source scrapée renvoie un blocage (HTTP 403) ou aucun
résultat, le scraper conserve les données existantes sans les écraser. La
source **`marketcheck` (API) est la voie fiable** pour des données réelles.

### Clé API Marketcheck

La source `marketcheck` interroge l'API REST de Marketcheck — données
structurées, sans blocage. Elle a besoin d'une clé :

1. Crée un compte développeur sur [marketcheck.com](https://www.marketcheck.com)
   et récupère ta clé API.
2. **En local** : `export MARKETCHECK_API_KEY="ta_clé"` avant de lancer le scraper.
3. **En CI** : dépôt → *Settings → Secrets and variables → Actions → New
   repository secret*, nom `MARKETCHECK_API_KEY`. Le workflow l'injecte
   automatiquement.

Sans clé, la source `marketcheck` est simplement ignorée (le scraper ne
plante pas). La clé n'est jamais stockée dans le dépôt.

### Clés API eBay Motors

La source `ebay` interroge la **Browse API** d'eBay — enchères et Buy-It-Now
filtrés sur les 458. Elle a besoin de deux identifiants (OAuth Client
Credentials) :

1. Crée une app sur [developer.ebay.com/my/keys](https://developer.ebay.com/my/keys)
   (compte développeur gratuit). Utilise le keyset **Production** :
   *App ID* = `EBAY_CLIENT_ID`, *Cert ID* = `EBAY_CLIENT_SECRET`.
2. **En local** : `export EBAY_CLIENT_ID="…"` et `export EBAY_CLIENT_SECRET="…"`.
3. **En CI** : ajoute deux secrets `EBAY_CLIENT_ID` et `EBAY_CLIENT_SECRET`
   dans *Settings → Secrets and variables → Actions*. Le workflow les injecte
   automatiquement.

Sans ces identifiants, la source `ebay` est ignorée silencieusement. Aucun
secret n'est stocké dans le dépôt.

L'endpoint REST par défaut (`mc-api.marketcheck.com/v2/search/car/active`) peut
être surchargé sans toucher au code via la variable `MARKETCHECK_ENDPOINT`,
si ton offre Marketcheck expose un hôte différent.

### Détection des bonnes affaires

`scraper/valuation.py` ajuste une **régression log-linéaire robuste** sur le
corpus — `ln(prix) ~ millésime + kilométrage + version` — pour estimer la
valeur de marché de chaque voiture. Les annonces aberrantes (prix d'appel
fantaisistes, erreurs de saisie) sont écartées de l'ajustement via un seuil
basé sur l'écart médian absolu, puis le modèle est ré-ajusté sur le cœur de
marché.

Le modèle expose son **imprécision** (`residual_pct`) : millésime, kilométrage
et version n'expliquent qu'une partie du prix — options, état et certification
lui échappent. Le tableau de bord calibre ses seuils sur cette marge : seuls
les écarts qui sortent nettement du bruit sont signalés « bonne affaire ». Un
écart fort reste une **piste à investiguer** (bonne affaire *ou* voiture à
vérifier), pas un verdict.

## Mise à jour automatique

Le workflow `.github/workflows/update-cote.yml` lance le scraper chaque jour
(et à la demande), puis publie `data/` si la cote a évolué. Les runners
GitHub Actions disposent d'un accès réseau, contrairement à certains
environnements de développement.

### Bouton « Mettre à jour » en un clic (optionnel)

Le tableau de bord affiche un bouton **« ↻ Mettre à jour les données »**. Par
défaut, il ouvre la page GitHub Actions du workflow (un clic là-bas suffit
pour lancer). Pour un vrai déclenchement *depuis* la page, un petit
**Cloudflare Worker** (`worker/update-cote-worker.js`) sert d'intermédiaire :

1. Crée un jeton GitHub *fine-grained* limité à `mickcoco987/delsoltahiti`
   avec la permission **Actions : Read and write**.
2. Déploie le Worker (tableau de bord Cloudflare → coller le fichier, ou
   `wrangler deploy` depuis `worker/`) et ajoute un **secret** `GH_TOKEN`
   avec ton jeton.
3. Recopie l'URL publique du Worker dans `config.js` (`updateEndpoint`).

Le bouton lance alors le workflow en un clic via `fetch()`. Un garde-fou
serveur refuse une relance si un run est déjà en cours ou date de moins de
5 min. Sans configuration, le bouton garde son comportement de lien.

## Structure

```
index.html, styles.css, app.js · config.js   Tableau de bord web + sélecteur
data/
  catalog.js                      Métadata multi-modèles pour le sélecteur
  <slug>/
    listings.json                 Annonces brutes du modèle
    history.json                  Points datés de la cote
    dashboard.js                  Bundle lu par le tableau de bord
scraper/
  catalog.py       Catalogue des modèles suivis (source de vérité)
  models.py        Modèle Listing + utilitaires
  aggregate.py     Calcul des statistiques de cote
  valuation.py     Estimation de valeur + détection des bonnes affaires
  store.py         Lecture/écriture des données et du bundle
  cli.py           Point d'entrée `python -m scraper`
  sources/
    base.py          Interface ListingSource
    html_json.py     Base de scraping (extraction du JSON embarqué)
    classic_com.py   Source scrapée (dealer)
    dupont_registry.py · rm_sothebys.py   Sources scrapées enchères (best-effort)
    marketcheck.py · ebay.py   Sources API (clés requises)
    sample.py        Échantillon de marché curé (Ferrari 458)
worker/
  update-cote-worker.js   Cloudflare Worker : déclenche le workflow en un clic
  wrangler.toml           Config minimale pour `wrangler deploy`
.github/workflows/update-cote.yml  Mise à jour quotidienne automatique (tous modèles)
```

### Ajouter un modèle

Ajouter une entrée dans `_CATALOG` du fichier `scraper/catalog.py` :
slug, marque, nom, plage de millésimes/prix/km, versions et règles de
classification, requêtes pour chaque source supportée. Aucune autre
modification n'est nécessaire — le sélecteur du tableau de bord et le workflow
CI prendront automatiquement le nouveau modèle en compte au prochain run.

## Repères de cote (marché US, printemps 2026)

| Version          | Millésimes | Fourchette indicative   |
|------------------|------------|-------------------------|
| 458 Italia (coupé) | 2010–2015 | ~150 000 – 270 000 $    |
| 458 Spider       | 2012–2015  | ~175 000 – 300 000 $    |
| 458 Speciale     | 2014–2015  | ~390 000 – 525 000 $+   |
| 458 Speciale A   | 2015       | ~900 000 $+ (très rare) |

La 458 — dernière Ferrari V8 atmosphérique largement diffusée — se montre
recherchée : marché orienté à la hausse, particulièrement pour les Speciale et
les exemplaires bien optionnés à faible kilométrage. Les prix restent
indicatifs et dépendent de l'état, des options et de l'historique d'entretien.
