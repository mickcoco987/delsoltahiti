"""Catalogue des modeles suivis - source de verite pour le scraper et l'UI.

Chaque entree decrit un modele auto (marque + version), avec :
- les bornes de plausibilite (millesimes, prix, kilometrage) ;
- la liste de ses versions (variants) et la regle de classification ;
- les requetes a passer a chaque source (eBay, Marketcheck, classic.com, ...) ;
- les filtres de titre pour ecarter les autres modeles.

Ajouter un modele = ajouter une entree dans `_CATALOG` ci-dessous.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class Model:
    """Description d'un modele auto suivi."""

    slug: str
    brand: str
    name: str               # libelle d'affichage (ex: "458 Italia")
    short_name: str         # version courte pour les titres (ex: "458")
    year_range: Tuple[int, int]
    price_range: Tuple[int, int]
    max_mileage: int
    variants: Tuple[str, ...]
    # Liste ordonnee : ((mots-cles), nom de variant). Premier match gagne.
    variant_rules: Tuple[Tuple[Tuple[str, ...], str], ...] = ()
    # Tokens devant apparaitre dans le titre/URL ; vide = pas de filtre.
    title_filter: Tuple[str, ...] = ()
    # Prefixes WMI du VIN (ex: "ZFF" Ferrari, "ZHW" Lamborghini Huracan).
    vin_prefixes: Tuple[str, ...] = ()
    # Configuration par source.
    ebay_query: str = ""
    marketcheck_make: str = ""
    marketcheck_models: Tuple[str, ...] = ()
    classic_pages: Tuple[str, ...] = ()
    dupont_live_pages: Tuple[str, ...] = ()
    rm_sothebys_pages: Tuple[str, ...] = ()

    @property
    def default_variant(self) -> str:
        return self.variants[0]

    def classify_variant(self, text: str) -> str:
        """Detecte la version a partir d'un titre/URL."""
        t = (text or "").lower()
        for keywords, variant in self.variant_rules:
            if any(k.lower() in t for k in keywords):
                return variant
        return self.default_variant

    def matches_title(self, text: str) -> bool:
        """Le texte parle-t-il bien de ce modele ? (filtre anti-bruit)."""
        if not self.title_filter:
            return True
        t = (text or "").lower()
        return any(token.lower() in t for token in self.title_filter)

    def title_for(self, year: int, variant: str) -> str:
        return f"{year} {self.brand} {self.short_name} {variant}".strip()


_CATALOG: Dict[str, Model] = {
    "ferrari-458": Model(
        slug="ferrari-458",
        brand="Ferrari",
        name="458 Italia",
        short_name="458",
        year_range=(2009, 2016),
        price_range=(40_000, 3_000_000),
        max_mileage=200_000,
        variants=("Italia", "Spider", "Speciale", "Speciale A"),
        variant_rules=(
            (("speciale a", "aperta"), "Speciale A"),
            (("speciale",), "Speciale"),
            (("spider", "spyder"), "Spider"),
        ),
        title_filter=("458",),
        vin_prefixes=("ZFF",),
        ebay_query="Ferrari 458",
        marketcheck_make="Ferrari",
        marketcheck_models=("458 Italia", "458 Spider", "458 Speciale"),
        classic_pages=(
            "https://www.classic.com/m/ferrari/458/coupe/",
            "https://www.classic.com/m/ferrari/458/spider/",
            "https://www.classic.com/m/ferrari/458/speciale/",
        ),
        dupont_live_pages=(
            "https://live.dupontregistry.com/listings/live/filter:sort=ending_soon",
        ),
        rm_sothebys_pages=("https://rmsothebys.com/results/",),
    ),
    "ferrari-f8": Model(
        slug="ferrari-f8",
        brand="Ferrari",
        name="F8 Tributo",
        short_name="F8",
        year_range=(2019, 2025),
        price_range=(180_000, 800_000),
        max_mileage=80_000,
        variants=("Tributo", "Spider"),
        variant_rules=(
            (("spider", "spyder"), "Spider"),
        ),
        title_filter=("f8",),
        vin_prefixes=("ZFF",),
        ebay_query="Ferrari F8",
        marketcheck_make="Ferrari",
        # Requete large : "F8" suffit, le title_filter ecarte le bruit.
        # ("F8 Tributo" et "F8 Spider" en exact match renvoyaient 0.)
        marketcheck_models=("F8",),
        classic_pages=(
            "https://www.classic.com/m/ferrari/f8/coupe/",
            "https://www.classic.com/m/ferrari/f8/spider/",
        ),
    ),
    "lamborghini-huracan": Model(
        slug="lamborghini-huracan",
        brand="Lamborghini",
        name="Huracan",
        short_name="Huracan",
        year_range=(2014, 2025),
        price_range=(120_000, 700_000),
        max_mileage=120_000,
        variants=("LP610-4", "Spyder", "Performante", "EVO", "STO", "Tecnica"),
        variant_rules=(
            (("sto",), "STO"),
            (("tecnica",), "Tecnica"),
            (("performante",), "Performante"),
            (("evo",), "EVO"),
            (("spyder", "spider"), "Spyder"),
        ),
        title_filter=("huracan", "huracán"),
        vin_prefixes=("ZHW",),
        ebay_query="Lamborghini Huracan",
        marketcheck_make="Lamborghini",
        marketcheck_models=("Huracan",),
        classic_pages=(
            "https://www.classic.com/m/lamborghini/huracan/coupe/",
            "https://www.classic.com/m/lamborghini/huracan/spyder/",
        ),
    ),
    "porsche-911-gt3": Model(
        slug="porsche-911-gt3",
        brand="Porsche",
        name="911 GT3",
        short_name="911 GT3",
        year_range=(2014, 2025),
        price_range=(120_000, 600_000),
        max_mileage=120_000,
        variants=("GT3", "GT3 Touring", "GT3 RS"),
        variant_rules=(
            (("gt3 rs", "gt3rs"), "GT3 RS"),
            (("touring",), "GT3 Touring"),
        ),
        title_filter=("gt3",),
        vin_prefixes=("WP0",),
        ebay_query="Porsche 911 GT3",
        marketcheck_make="Porsche",
        marketcheck_models=("911",),
        classic_pages=(
            "https://www.classic.com/m/porsche/911/991/gt3/",
            "https://www.classic.com/m/porsche/911/992/gt3/",
        ),
    ),
}


def get_model(slug: str) -> Model:
    if slug not in _CATALOG:
        raise KeyError(
            f"Modele inconnu : {slug!r}. Modeles disponibles : {list(_CATALOG)}"
        )
    return _CATALOG[slug]


def all_models() -> List[Model]:
    return list(_CATALOG.values())


def all_slugs() -> List[str]:
    return list(_CATALOG.keys())
