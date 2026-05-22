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
  (classic.com, Bring a Trailer, cars.com) et tient à jour un historique de cote.
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
python3 -m scraper --source all        # toutes les sources live (défaut)
python3 -m scraper --source bat        # une seule source : Bring a Trailer
python3 -m scraper --source sample     # données d'échantillon curées
python3 -m scraper --seed              # réinitialise tout depuis l'échantillon
python3 -m scraper --source all --replace -v
```

À chaque exécution, le scraper agrège les annonces, **estime la valeur de
marché de chacune** et détecte les bonnes affaires, recalcule les statistiques
(moyenne, médiane, fourchette, par version, par millésime) et ajoute un point
daté à l'historique de cote.

### Sources de données

| Source    | Description                                                        |
|-----------|--------------------------------------------------------------------|
| `classic` | classic.com — agrégateur de cote du marché US.                     |
| `bat`     | Bring a Trailer — enchères et résultats de ventes réels.           |
| `cars`    | cars.com — annonces de concessionnaires et de particuliers.        |
| `all`     | Enchaîne les trois sources live ci-dessus (défaut).                |
| `sample`  | Relevés de marché curés (classic.com, Edmunds, cars.com, Hagerty). |

Les sources live partagent la base `HtmlJsonSource` : elle extrait le JSON
embarqué des pages (JSON-LD, données Next.js, autres blocs `application/json`)
et le parcourt récursivement. Tant que les données restent dans un JSON de la
page, le scraper résiste aux changements de mise en page. Ajouter une source =
sous-classer `HtmlJsonSource` (`name`, `base_url`, `pages`).

**Limite connue** : les sites d'annonces appliquent des protections anti-bot.
Si les sources live renvoient un blocage (HTTP 403) ou aucun résultat, le
scraper conserve les données existantes sans les écraser — utilisez alors
`--source sample`.

### Détection des bonnes affaires

`scraper/valuation.py` ajuste une **régression log-linéaire** sur le corpus
d'annonces — `ln(prix) ~ millésime + kilométrage + version` — pour estimer la
valeur de marché de chaque voiture. L'écart entre le prix demandé et cette
estimation donne le score : une annonce nettement sous la valeur estimée est
mise en avant dans la section « Bonnes affaires » du tableau de bord.

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
    classic_com.py · bring_a_trailer.py · cars_com.py   Sources live
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
