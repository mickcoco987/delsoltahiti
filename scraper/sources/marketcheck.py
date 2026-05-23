"""Source API Marketcheck - inventaire de vehicules a vendre aux Etats-Unis.

Contrairement aux sources scrapees, Marketcheck expose une API REST stable :
donnees structurees, usage prevu pour ca, sans blocage anti-bot. C'est la
source la plus fiable pour des donnees reelles et fraiches.

Necessite une cle API (inscription developpeur sur https://www.marketcheck.com),
fournie via la variable d'environnement MARKETCHECK_API_KEY. Sans cle, la
source est simplement ignoree (elle ne fait pas echouer le scraper).

Endpoint par defaut : API v2 `search/car/active`. Surchargeable sans toucher
au code via la variable d'environnement MARKETCHECK_ENDPOINT (utile si votre
offre Marketcheck expose un hote different).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import Listing, classify_variant, parse_int
from .base import ListingSource

log = logging.getLogger(__name__)

_DEFAULT_ENDPOINT = "https://mc-api.marketcheck.com/v2/search/car/active"
_MODELS = ["458 Italia", "458 Spider", "458 Speciale"]
_ROWS = 50            # maximum de resultats par requete
_MAX_PER_MODEL = 200  # plafond d'annonces collectees par modele

MIN_PRICE = 40_000
MAX_PRICE = 3_000_000
MAX_MILEAGE = 200_000


class MarketcheckSource(ListingSource):
    name = "marketcheck"

    def __init__(self, api_key: Optional[str] = None,
                 endpoint: Optional[str] = None, timeout: int = 25):
        self.api_key = api_key or os.environ.get("MARKETCHECK_API_KEY", "")
        self.endpoint = endpoint or os.environ.get(
            "MARKETCHECK_ENDPOINT", _DEFAULT_ENDPOINT)
        self.timeout = timeout

    def fetch(self) -> List[Listing]:
        if not self.api_key:
            log.warning(
                "marketcheck : variable MARKETCHECK_API_KEY absente, source "
                "ignoree. Obtenez une cle sur marketcheck.com puis exportez-la "
                "(ou ajoutez-la en secret GitHub Actions)."
            )
            return []
        listings: List[Listing] = []
        seen: set[str] = set()
        for model in _MODELS:
            listings.extend(self._fetch_model(model, seen))
        log.info("marketcheck : %d annonces au total", len(listings))
        return listings

    def _fetch_model(self, model: str, seen: set) -> List[Listing]:
        collected: List[Listing] = []
        start = 0
        while start < _MAX_PER_MODEL:
            params = {
                "api_key": self.api_key,
                "make": "Ferrari",
                "model": model,
                "car_type": "used",
                "country": "US",
                "rows": _ROWS,
                "start": start,
            }
            try:
                payload = self._get_json(self.endpoint + "?" + urlencode(params))
            except (HTTPError, URLError, OSError, ValueError) as exc:
                log.warning("marketcheck : echec de la requete '%s' (%s)",
                            model, exc)
                break
            rows = payload.get("listings") or []
            if not rows:
                break
            for raw in rows:
                listing = self._to_listing(raw)
                if listing and listing.id not in seen:
                    seen.add(listing.id)
                    collected.append(listing)
            if len(rows) < _ROWS:
                break
            start += _ROWS
        log.info("marketcheck : '%s' -> %d annonces", model, len(collected))
        return collected

    def _get_json(self, url: str) -> dict:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "delsoltahiti-cote/1.0",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))

    @staticmethod
    def _to_listing(raw: dict) -> Optional[Listing]:
        if not isinstance(raw, dict):
            return None
        build = raw.get("build") or {}
        year = parse_int(build.get("year"))
        if not year or not (2009 <= year <= 2016):
            return None

        price = parse_int(raw.get("price"))
        if not price or not (MIN_PRICE <= price <= MAX_PRICE):
            return None

        mileage = parse_int(raw.get("miles"))
        if mileage is not None and mileage > MAX_MILEAGE:
            mileage = None

        trim = build.get("trim") or ""
        variant = classify_variant(f"{build.get('model', '')} {trim}")

        dealer = raw.get("dealer") or {}
        location = ", ".join(
            part for part in (dealer.get("city"), dealer.get("state")) if part
        )

        # Statut de titre si Marketcheck le renvoie (champ Carfax).
        clean = raw.get("carfax_clean_title")

        # Date de mise en ligne : `first_seen_at` est un timestamp Unix UTC.
        posted_at = _to_iso_date(raw.get("first_seen_at"))

        return Listing(
            year=year,
            variant=variant,
            price=price,
            mileage=mileage,
            title=f"{year} Ferrari 458 {variant}",
            url=raw.get("vdp_url") or "",
            source="marketcheck",
            location=location,
            status="for_sale",
            vin=str(raw.get("vin") or ""),
            clean_title=clean if isinstance(clean, bool) else None,
            posted_at=posted_at,
        )


def _to_iso_date(value) -> Optional[str]:
    """Convertit un timestamp Marketcheck (Unix ou ISO) en date YYYY-MM-DD."""
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d")
    if isinstance(value, str) and len(value) >= 10:
        # Accepte deja un ISO type "2026-05-10T..." -> prend la portion date.
        return value[:10]
    return None
