"""Point d'entree CLI : `python -m scraper`.

Exemples :
    python -m scraper --seed              # amorce les donnees (echantillon cure)
    python -m scraper --source classic    # scrape la cote live sur classic.com
    python -m scraper --source sample     # regenere a partir de l'echantillon
"""

from __future__ import annotations

import argparse
import logging
from typing import List

from .aggregate import build_market
from .models import Listing
from .sources.classic_com import ClassicComSource
from .sources.sample import SampleSource
from . import store

log = logging.getLogger("scraper")

SOURCES = {
    "classic": ClassicComSource,
    "sample": SampleSource,
}


def _merge(existing: List[Listing], scraped: List[Listing]) -> List[Listing]:
    """Fusionne les annonces scrapees par-dessus les existantes (cle = id)."""
    by_id = {l.id: l for l in existing}
    for listing in scraped:
        by_id[listing.id] = listing
    return list(by_id.values())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="Suivi de la cote des Ferrari 458 Italia sur le marche US.",
    )
    parser.add_argument(
        "--source", choices=list(SOURCES), default="classic",
        help="Source de donnees (defaut : classic).",
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

    source = SOURCES[args.source]()
    log.info("Collecte de la cote depuis : %s", source.name)
    scraped = source.fetch()

    if not scraped:
        log.warning("Aucune annonce recuperee depuis %s.", source.name)
        if args.source == "classic":
            log.warning(
                "La source live n'a rien renvoye (blocage anti-bot ou changement "
                "de structure du site). Donnees existantes conservees. "
                "Repli possible : python -m scraper --source sample"
            )
        return 1

    existing = [] if args.replace else store.load_listings()
    listings = scraped if args.replace else _merge(existing, scraped)

    market = build_market(listings)

    if args.seed and isinstance(source, SampleSource):
        history = source.history()
    else:
        history = store.load_history()
    history = store.append_history(history, market)

    store.save(listings, history, sources=[source.name])

    overall = market["overall"]
    log.info(
        "Cote mise a jour : %d annonces | prix moyen %s $ | mediane %s $ | "
        "fourchette %s - %s $",
        overall["count"],
        f"{overall['avg_price']:,}".replace(",", " "),
        f"{overall['median_price']:,}".replace(",", " "),
        f"{overall['min_price']:,}".replace(",", " "),
        f"{overall['max_price']:,}".replace(",", " "),
    )
    return 0
