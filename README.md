# Cote Ferrari 458 Italia — marché US

Suivi de la **cote des Ferrari 458** (Italia, Spider, Speciale, Speciale A) sur
le marché des États-Unis : un scraper automatisé collecte les annonces et un
tableau de bord web affiche l'évolution de la valeur.

## Aperçu

- **Tableau de bord** (`index.html`) : indicateurs de cote, évolution dans le
  temps, prix par millésime, prix vs kilométrage et liste des annonces. 100 %
  HTML/CSS/JS, graphiques en SVG, sans dépendance externe.
- **Scraper** (`scraper/`) : outil Python (bibliothèque standard uniquement,
  aucune installation requise) qui agrège les annonces et tient à jour un
  historique de cote.
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
python3 -m scraper --source classic    # cote live depuis classic.com
python3 -m scraper --source sample     # données d'échantillon curées
python3 -m scraper --seed              # réinitialise tout depuis l'échantillon
python3 -m scraper --source classic --replace -v
```

À chaque exécution, le scraper met à jour les annonces, recalcule les
statistiques (moyenne, médiane, fourchette, par version, par millésime) et
ajoute un point daté à l'historique de cote.

### Sources de données

| Source     | Description                                                        |
|------------|--------------------------------------------------------------------|
| `classic`  | Scrape classic.com (agrégateur de cote du marché US).              |
| `sample`   | Relevés de marché curés (classic.com, Edmunds, cars.com, Hagerty). |

Le scraper `classic.com` extrait le JSON embarqué des pages (JSON-LD puis
données Next.js) et le parcourt récursivement : tant que les données restent
dans un JSON de la page, il résiste aux changements de mise en page.

**Limite connue** : les sites d'annonces appliquent des protections anti-bot.
Si la source live renvoie un blocage (HTTP 403) ou aucun résultat, le scraper
conserve les données existantes sans les écraser — utilisez alors
`--source sample`. Ajouter une source = sous-classer `ListingSource`
(`scraper/sources/base.py`).

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
  store.py         Lecture/écriture des données et du bundle
  cli.py           Point d'entrée `python -m scraper`
  sources/         Sources de données (classic.com, échantillon)
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
