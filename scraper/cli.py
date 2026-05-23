"""Point d'entree CLI : `python -m scraper`.

Exemples :
    python -m scraper --seed              # amorce les donnees (echantillon cure)
    python -m scraper --source all        # classic.com + BaT + Marketcheck
    python -m scraper --source marketcheck  # une seule source (API, cle requise)
    python -m scraper --source sample     # regenere a partir de l'echantillon
"""

from __future__ import annotations

import argparse
import logging
from typing import List

from .aggregate import build_market
from .models import Listing
from .sources.classic_com import ClassicComSource
from .sources.dupont_registry import DupontRegistryLiveSource
from .sources.dupont_registry_autos import DupontRegistryAutosSource
from .sources.ebay import EbayMotorsSource
from .sources.hemmings import HemmingsSource
from .sources.marketcheck import MarketcheckSource
from .sources.rm_sothebys import RmSothebysSource
from .sources.sample import SampleSource
from .valuation import fit_model, score_listings
from . import store

log = logging.getLogger("scraper")

# Sources live (sites reels). `all` les enchaine toutes.
LIVE_SOURCES = {
    "classic": ClassicComSource,
    "marketcheck": MarketcheckSource,
    "ebay": EbayMotorsSource,
    "dupont": DupontRegistryLiveSource,
    "dupont-autos": DupontRegistryAutosSource,
    "hemmings": HemmingsSource,
    "sothebys": RmSothebysSource,
}
SOURCES = {**LIVE_SOURCES, "sample": SampleSource}


def _merge(existing: List[Listing], scraped: List[Listing]) -> List[Listing]:
    """Fusionne les annonces scrapees par-dessus les existantes (cle = id)."""
    by_id = {l.id: l for l in existing}
    for listing in scraped:
        by_id[listing.id] = listing
    return list(by_id.values())


def _collect(source_arg: str):
    """Renvoie (annonces, noms des sources ayant repondu)."""
    if source_arg == "all":
        instances = [cls() for cls in LIVE_SOURCES.values()]
    else:
        instances = [SOURCES[source_arg]()]

    scraped: List[Listing] = []
    responded: List[str] = []
    for source in instances:
        log.info("Collecte de la cote depuis : %s", source.name)
        items = source.fetch()
        if items:
            responded.append(source.name)
            scraped.extend(items)
        else:
            log.warning("Aucune annonce recuperee depuis %s.", source.name)
    return scraped, responded


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="Suivi de la cote des Ferrari 458 Italia sur le marche US.",
    )
    parser.add_argument(
        "--source", choices=list(SOURCES) + ["all"], default="all",
        help="Source de donnees (defaut : all = toutes les sources live).",
    )
    parser.add_argument(
        "--replace", action="store_true",
        help="Remplace les annonces existantes au lieu de fusionner.",
    )
    parser.add_argument(
        "--seed", action="store_true",
        help="Reinitialise les donnees a partir de l'echantillon cure.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.seed:
        args.source = "sample"
        args.replace = True

    scraped, responded = _collect(args.source)

    if not scraped:
        log.warning("Aucune annonce recuperee.")
        if args.source != "sample":
            log.warning(
                "Les sources live n'ont rien renvoye (blocage anti-bot ou "
                "changement de structure). Donnees existantes conservees. "
                "Repli possible : python -m scraper --source sample"
            )
        return 1

    existing = [] if args.replace else store.load_listings()
    listings = scraped if args.replace else _merge(existing, scraped)

    # Estimation de valeur et detection des bonnes affaires.
    model = fit_model(listings)
    score_listings(listings, model)
    log.info("Modele de valeur : %s", model.method)

    market = build_market(listings)

    # L'historique de cote ne se construit que sur des mesures reelles ;
    # `--seed` repart donc d'un historique vide.
    history = [] if args.seed else store.load_history()
    history = store.append_history(history, market)

    store.save(listings, history, sources=responded,
               valuation={"method": model.method,
                          "residual_pct": model.residual_pct})

    overall = market["overall"]
    deals = [l for l in listings if l.status == "for_sale"
             and l.deal_pct is not None and l.deal_pct >= 7]
    log.info(
        "Cote mise a jour : %d annonces | prix moyen %s $ | %d bonne(s) affaire(s)",
        overall["count"],
        f"{overall['avg_price']:,}".replace(",", " "),
        len(deals),
    )
    return 0
