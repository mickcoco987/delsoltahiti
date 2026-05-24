"""Point d'entree CLI : `python -m scraper`.

Exemples :
    python -m scraper --seed                              # amorce Ferrari 458
    python -m scraper --model ferrari-458 --source all    # tous les sources
    python -m scraper --model lamborghini-huracan         # autre modele
    python -m scraper --model all --replace               # boucle sur tous
"""

from __future__ import annotations

import argparse
import logging
from typing import List

from .aggregate import build_market
from .catalog import Model, all_models, all_slugs, get_model
from .models import Listing
from .sources.classic_com import ClassicComSource
from .sources.dupont_registry import DupontRegistryLiveSource
from .sources.ebay import EbayMotorsSource
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
    "sothebys": RmSothebysSource,
}
SOURCES = {**LIVE_SOURCES, "sample": SampleSource}


def _merge(existing: List[Listing], scraped: List[Listing]) -> List[Listing]:
    """Fusionne les annonces scrapees par-dessus les existantes (cle = id)."""
    by_id = {l.id: l for l in existing}
    for listing in scraped:
        by_id[listing.id] = listing
    return list(by_id.values())


def _collect(model: Model, source_arg: str):
    """Renvoie (annonces, noms des sources ayant repondu) pour un modele."""
    if source_arg == "all":
        instances = [cls(model) for cls in LIVE_SOURCES.values()]
    else:
        instances = [SOURCES[source_arg](model)]

    scraped: List[Listing] = []
    responded: List[str] = []
    for source in instances:
        log.info("[%s] Collecte de la cote depuis : %s", model.slug, source.name)
        items = source.fetch()
        if items:
            responded.append(source.name)
            scraped.extend(items)
        else:
            log.warning("[%s] Aucune annonce recuperee depuis %s.",
                        model.slug, source.name)
    return scraped, responded


def _run_model(model: Model, args) -> int:
    scraped, responded = _collect(model, args.source)

    if not scraped:
        log.warning("[%s] Aucune annonce recuperee.", model.slug)
        if args.source != "sample":
            log.warning(
                "[%s] Les sources live n'ont rien renvoye. Donnees existantes "
                "conservees. Repli possible : python -m scraper --model %s "
                "--source sample", model.slug, model.slug,
            )
        return 1

    existing = [] if args.replace else store.load_listings(model)
    listings = scraped if args.replace else _merge(existing, scraped)

    valuation_model = fit_model(listings, model)
    score_listings(listings, valuation_model)
    log.info("[%s] Modele de valeur : %s", model.slug, valuation_model.method)

    market = build_market(listings, model)

    # L'historique de cote ne se construit que sur des mesures reelles ;
    # `--seed` repart donc d'un historique vide.
    history = [] if args.seed else store.load_history(model)
    history = store.append_history(history, market)

    store.save(model, listings, history, sources=responded,
               valuation={"method": valuation_model.method,
                          "residual_pct": valuation_model.residual_pct})

    overall = market["overall"]
    deals = [l for l in listings if l.status == "for_sale"
             and l.deal_pct is not None and l.deal_pct >= 7]
    avg_price = overall["avg_price"]
    log.info(
        "[%s] Cote mise a jour : %d annonces | prix moyen %s $ | %d bonne(s) affaire(s)",
        model.slug, overall["count"],
        f"{avg_price:,}".replace(",", " ") if avg_price else "—",
        len(deals),
    )
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="Suivi de la cote de supercars sur le marche US (multi-modeles).",
    )
    parser.add_argument(
        "--model", default="ferrari-458",
        help=("Modele a scraper (slug). 'all' = tous les modeles du catalogue. "
              "Modeles disponibles : " + ", ".join(all_slugs()) + "."),
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
        help=("Reinitialise les donnees depuis l'echantillon cure "
              "(Ferrari 458 uniquement)."),
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
        if args.model == "all":
            args.model = "ferrari-458"

    if args.model == "all":
        models = all_models()
    else:
        try:
            models = [get_model(args.model)]
        except KeyError as exc:
            log.error(str(exc))
            return 2

    exit_codes = []
    for model in models:
        exit_codes.append(_run_model(model, args))

    # Le catalogue est toujours regenere (refleter les `has_data` a jour).
    store.write_catalog(all_models())

    return 0 if 0 in exit_codes else exit_codes[-1]
