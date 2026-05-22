"""Modele de valeur de marche et detection des bonnes affaires.

Une regression log-lineaire est ajustee sur le corpus d'annonces :

    ln(prix) = b0 + b_annee*(annee-2012) + b_km*(km/1000) + offsets de version

La valeur estimee d'une annonce est sa prediction par le modele. L'ecart entre
le prix demande et cette valeur estimee donne le score de bonne affaire :
un prix nettement sous l'estimation = annonce sous la cote du marche.

Le travail en espace logarithmique gere naturellement les ecarts d'echelle
entre une Italia (~200 k$) et une Speciale A (~1 M$).
"""

from __future__ import annotations

import math
from statistics import median
from typing import List, Optional

from .models import Listing, VARIANTS

_REF_YEAR = 2012
_N_FEATURES = 6


def _features(variant: str, year: int, mileage: float) -> List[float]:
    """Vecteur de caracteristiques (Italia = version de reference)."""
    return [
        1.0,
        year - _REF_YEAR,
        mileage / 1000.0,
        1.0 if variant == "Spider" else 0.0,
        1.0 if variant == "Speciale" else 0.0,
        1.0 if variant == "Speciale A" else 0.0,
    ]


def _solve(matrix: List[List[float]], vector: List[float]) -> Optional[List[float]]:
    """Resout un systeme lineaire par elimination de Gauss avec pivot partiel."""
    n = len(vector)
    aug = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        divisor = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= divisor
        for r in range(n):
            if r != col and aug[r][col]:
                factor = aug[r][col]
                for j in range(col, n + 1):
                    aug[r][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


class _OlsModel:
    method = "regression log-lineaire (millesime + kilometrage + version)"

    def __init__(self, beta: List[float], median_km: dict):
        self.beta = beta
        self.median_km = median_km

    def estimate(self, variant: str, year: int, mileage: Optional[int]) -> int:
        if not mileage or mileage <= 0:
            mileage = self.median_km.get(variant, 12000)
        x = _features(variant, year, mileage)
        ln_price = sum(b * xi for b, xi in zip(self.beta, x))
        return int(round(math.exp(ln_price)))


class _FallbackModel:
    """Repli quand le corpus est trop maigre pour une regression fiable."""

    method = "comparables par version (corpus limite)"

    def __init__(self, rows: List[Listing], median_km: dict):
        self.median_km = median_km
        self.base_price = {}
        self.base_year = {}
        for variant in VARIANTS:
            prices = [l.price for l in rows if l.variant == variant]
            years = [l.year for l in rows if l.variant == variant]
            self.base_price[variant] = median(prices) if prices else None
            self.base_year[variant] = median(years) if years else 2013
        self._global = median([l.price for l in rows]) if rows else 200000

    def estimate(self, variant: str, year: int, mileage: Optional[int]) -> int:
        base = self.base_price.get(variant) or self._global
        ref_km = self.median_km.get(variant, 12000)
        if not mileage or mileage <= 0:
            mileage = ref_km
        km_factor = max(0.4, 1 - 0.004 * ((mileage - ref_km) / 1000.0))
        year_factor = max(0.6, 1 + 0.03 * (year - self.base_year.get(variant, 2013)))
        return int(round(base * km_factor * year_factor))


def fit_model(listings: List[Listing]):
    """Ajuste un modele de valeur sur les annonces disposant d'un prix et d'un km."""
    rows = [
        l for l in listings
        if l.price and l.price > 0 and l.mileage and l.mileage > 0 and l.year
    ]
    all_km = [l.mileage for l in rows]
    median_km = {}
    for variant in VARIANTS:
        kms = [l.mileage for l in rows if l.variant == variant]
        median_km[variant] = median(kms) if kms else (
            median(all_km) if all_km else 12000
        )

    if len(rows) < 2 * _N_FEATURES:
        return _FallbackModel(rows, median_km)

    xt_x = [[0.0] * _N_FEATURES for _ in range(_N_FEATURES)]
    xt_y = [0.0] * _N_FEATURES
    for listing in rows:
        x = _features(listing.variant, listing.year, listing.mileage)
        ln_price = math.log(listing.price)
        for a in range(_N_FEATURES):
            xt_y[a] += x[a] * ln_price
            for b in range(_N_FEATURES):
                xt_x[a][b] += x[a] * x[b]
    for a in range(_N_FEATURES):
        xt_x[a][a] += 1e-6  # regularisation pour la stabilite numerique

    beta = _solve(xt_x, xt_y)
    if beta is None:
        return _FallbackModel(rows, median_km)
    return _OlsModel(beta, median_km)


def score_listings(listings: List[Listing], model) -> List[Listing]:
    """Annote chaque annonce avec sa valeur estimee et son ecart a la cote.

    `deal_pct` positif = prix demande sous la valeur estimee (bonne affaire).
    """
    for listing in listings:
        if not listing.price or listing.price <= 0:
            listing.estimated_value = None
            listing.deal_pct = None
            continue
        estimate = model.estimate(listing.variant, listing.year, listing.mileage)
        listing.estimated_value = estimate
        listing.deal_pct = (
            round((estimate - listing.price) / estimate * 100, 1)
            if estimate else None
        )
    return listings
