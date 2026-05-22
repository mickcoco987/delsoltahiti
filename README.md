# Cote Ferrari 458 Italia — marché US

Suivi de la **cote des Ferrari 458** (Italia, Spider, Speciale, Speciale A) sur
le marché des États-Unis : un scraper automatisé collecte les annonces et un
tableau de bord web affiche l'évolution de la valeur.

## Aperçu

- **Tableau de bord** (`index.html`) : section **bonnes affaires**, indicateurs
  de cote, évolution dans le temps, prix par millésime, prix vs kilométrage et
  liste des annonces. 100 % HTML/CSS/JS, graphiques en SVG, sans dépendance.
- **Scraper** (`scraper/`) : outil Python (bibliothèque standard uniquement,
  aucune installation requise) qui agrège les annonces de plusieurs sources
  (classic.com, Bring a Trailer, API Marketcheck) et tient à jour un historique
  de cote.
- **Moteur de valeur** (`scraper/valuation.py`) : estime la valeur de marché de
  chaque annonce et repère celles **sous la cote** (outil de sourcing).
- **Données** (`data/`) : `listings.json`, `history.json` et `dashboard.js`
  (le bundle lu par le tableau de bord), régénérés par le scraper.

## Démarrage rapide

```sh
# 1. Amorcer les données (échantillon de marché curé)
python3 -m scraper --seed

# 2. Servir le tableau de bord
python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

> Le tableau de bord lit `data/dashboard.js` via une balise `<script>`, il
> fonctionne donc aussi en ouvrant `index.html` directement (sans serveur).

## Le scraper

```sh
python3 -m scraper --source all          # toutes les sources live (défaut)
python3 -m scraper --source marketcheck  # source API seule (clé requise)
python3 -m scraper --source sample       # données d'échantillon curées
python3 -m scraper --seed                # réinitialise depuis l'échantillon
python3 -m scraper --source all --replace -v
```

À chaque exécution, le scraper agrège les annonces, **estime la valeur de
marché de chacune** et détecte les bonnes affaires, recalcule les statistiques
(moyenne, médiane, fourchette, par version, par millésime) et ajoute un point
daté à l'historique de cote.

### Sources de données

| Source        | Type    | Description                                          |
|---------------|---------|------------------------------------------------------|
| `classic`     | scrape  | classic.com — agrégateur de cote du marché US.       |
| `bat`         | scrape  | Bring a Trailer — enchères et résultats de ventes.   |
| `marketcheck` | **API** | Marketcheck — inventaire US (fiable, clé requise).   |
| `all`         | —       | Enchaîne les trois sources live ci-dessus (défaut).  |
| `sample`      | local   | Relevés de marché curés (échantillon de démarrage).  |

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

## Structure

```
index.html, styles.css, app.js   Tableau de bord web
data/                            listings.json · history.json · dashboard.js
scraper/
  models.py        Modèle Listing + utilitaires
  aggregate.py     Calcul des statistiques de cote
  valuation.py     Estimation de valeur + détection des bonnes affaires
  store.py         Lecture/écriture des données et du bundle
  cli.py           Point d'entrée `python -m scraper`
  sources/
    base.py          Interface ListingSource
    html_json.py     Base de scraping (extraction du JSON embarqué)
    classic_com.py · bring_a_trailer.py   Sources scrapées
    marketcheck.py   Source API Marketcheck (clé requise)
    sample.py        Échantillon de marché curé
.github/workflows/update-cote.yml  Mise à jour quotidienne automatique
```

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
