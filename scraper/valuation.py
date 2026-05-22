"""Modele de valeur de marche et detection des bonnes affaires.

Une regression log-lineaire est ajustee sur le corpus d'annonces :

    ln(prix) = b0 + b_annee*(annee-2012) + b_km*(km/1000) + offsets de version

L'ajustement est *robuste* : apres une premiere passe, les annonces dont le
residu s'ecarte trop du marche (prix d'appel fantaisistes, erreurs de saisie)
sont ecartees du calcul via un seuil base sur l'ecart median absolu (MAD),
lui-meme insensible aux aberrations ; le modele est ensuite re-ajuste sur le
coeur de marche. Ces annonces restent evaluees et notees.

Le modele expose aussi son **imprecision** (`residual_pct`) : l'echelle des
residus du coeur de marche. Le millesime, le kilometrage et la version
n'expliquent qu'une partie du prix (options, etat, certification echappent au
modele), donc une estimation n'est fiable qu'a +/- cette marge pres. Le
tableau de bord calibre ses seuils de bonne affaire sur cette valeur.

Le travail en espace logarithmique gere les ecarts d'echelle entre une Italia
(~200 k$) et une Speciale A (~1 M$).
"""

from __future__ import annotations

import logging
import math
from statistics import median
from typing import List, Optional, Tuple

from .models import Listing, VARIANTS

log = logging.getLogger(__name__)

_REF_YEAR = 2012
_N_FEATURES = 6
_MIN_ROWS = 2 * _N_FEATURES   # corpus minimal pour une regression fiable
_OUTLIER_K = 2.5              # seuil de rejet, en echelles robustes (MAD)
_MAX_TRIM_PASSES = 3
_MIN_SIGMA = 0.04             # plancher d'imprecision (evite des seuils degeneres)


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


def _predict_ln(beta: List[float], variant: str, year: int, mileage: float) -> float:
    return sum(b * xi for b, xi in zip(beta, _features(variant, year, mileage)))


def _fit_ols(rows: List[Listing]) -> Optional[List[float]]:
    """Ajuste une regression OLS en espace log. Renvoie beta, ou None."""
    if len(rows) < _MIN_ROWS:
        return None
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
    return _solve(xt_x, xt_y)


def _residuals(rows: List[Listing], beta: List[float]) -> List[float]:
    return [
        math.log(l.price) - _predict_ln(beta, l.variant, l.year, l.mileage)
        for l in rows
    ]


def _robust_scale(values: List[float]) -> Tuple[float, float]:
    """Centre et echelle robustes (mediane, MAD), insensibles aux aberrations."""
    center = median(values)
    mad = median([abs(v - center) for v in values])
    return center, 1.4826 * mad  # 1.4826 : MAD -> equivalent ecart-type normal


class _OlsModel:
    def __init__(self, beta: List[float], median_km: dict, sigma: float,
                 robust: bool):
        self.beta = beta
        self.median_km = median_km
        # Imprecision du modele : echelle des residus convertie en pourcentage.
        self.residual_pct = round((math.exp(max(sigma, _MIN_SIGMA)) - 1) * 100, 1)
        self.method = (
            "regression log-lineaire robuste (millesime + kilometrage + version)"
            if robust else
            "regression log-lineaire (millesime + kilometrage + version)"
        )

    def estimate(self, variant: str, year: int, mileage: Optional[int]) -> int:
        if not mileage or mileage <= 0:
            mileage = self.median_km.get(variant, 12000)
        return int(round(math.exp(_predict_ln(self.beta, variant, year, mileage))))


class _FallbackModel:
    """Repli quand le corpus est trop maigre pour une regression fiable."""

    method = "comparables par version (corpus limite)"
    residual_pct = 22.0

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
    """Ajuste un modele de valeur robuste sur les annonces prix + km connus."""
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

    beta = _fit_ols(rows)
    if beta is None:
        return _FallbackModel(rows, median_km)

    # Passes robustes : on ecarte les annonces trop eloignees du marche
    # (prix d'appel fantaisistes, erreurs), puis on re-ajuste sur le coeur.
    kept = rows
    for _ in range(_MAX_TRIM_PASSES):
        center, scale = _robust_scale(_residuals(kept, beta))
        if scale <= 0:
            break
        cleaned = [
            l for l, r in zip(kept, _residuals(kept, beta))
            if abs(r - center) <= _OUTLIER_K * scale
        ]
        if len(cleaned) == len(kept) or len(cleaned) < _MIN_ROWS:
            break
        refined = _fit_ols(cleaned)
        if refined is None:
            break
        kept, beta = cleaned, refined

    # Imprecision du modele : echelle robuste des residus du coeur de marche.
    _, sigma = _robust_scale(_residuals(kept, beta))
    trimmed = len(rows) - len(kept)
    if trimmed:
        log.info("valuation : %d annonce(s) aberrante(s) ecartee(s) de "
                 "l'ajustement (sur %d)", trimmed, len(rows))
    return _OlsModel(beta, median_km, sigma, robust=trimmed > 0)


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
