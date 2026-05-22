"""Calcul des statistiques de cote a partir des annonces."""

from __future__ import annotations

import statistics
from typing import Iterable, List, Optional

from .models import Listing, VARIANTS


def _stats(prices: List[int], mileages: List[int]) -> dict:
    prices = sorted(p for p in prices if p)
    mileages = sorted(m for m in mileages if m)
    if not prices:
        return {
            "count": 0,
            "avg_price": None,
            "median_price": None,
            "min_price": None,
            "max_price": None,
            "avg_mileage": None,
        }
    return {
        "count": len(prices),
        "avg_price": round(statistics.mean(prices)),
        "median_price": round(statistics.median(prices)),
        "min_price": prices[0],
        "max_price": prices[-1],
        "avg_mileage": round(statistics.mean(mileages)) if mileages else None,
    }


def build_market(listings: Iterable[Listing]) -> dict:
    """Construit le bloc de statistiques globales / par version / par millesime."""
    listings = list(listings)

    overall = _stats([l.price for l in listings], [l.mileage for l in listings])

    by_variant = {}
    for variant in VARIANTS:
        subset = [l for l in listings if l.variant == variant]
        by_variant[variant] = _stats(
            [l.price for l in subset], [l.mileage for l in subset]
        )

    by_year = {}
    for year in sorted({l.year for l in listings}):
        subset = [l for l in listings if l.year == year]
        by_year[str(year)] = _stats(
            [l.price for l in subset], [l.mileage for l in subset]
        )

    return {"overall": overall, "by_variant": by_variant, "by_year": by_year}
