"""Source API Marketcheck - inventaire de vehicules a vendre aux Etats-Unis.

Contrairement aux sources scrapees, Marketcheck expose une API REST stable :
donnees structurees, usage prevu pour ca, sans blocage anti-bot. C'est la
source la plus fiable pour des donnees reelles et fraiches.

Necessite une cle API (inscription developpeur sur https://www.marketcheck.com),
fournie via la variable d'environnement MARKETCHECK_API_KEY. Sans cle, la
source est simplement ignoree (elle ne fait pas echouer le scraper).

Endpoint par defaut : API v2 `search/car/active`. Surchargeable via
MARKETCHECK_ENDPOINT.
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

from ..catalog import Model
from ..models import Listing, parse_int
from .base import ListingSource

log = logging.getLogger(__name__)

_DEFAULT_ENDPOINT = "https://mc-api.marketcheck.com/v2/search/car/active"
_ROWS = 50            # maximum de resultats par requete
_MAX_PER_MODEL = 200  # plafond d'annonces collectees par modele


class MarketcheckSource(ListingSource):
    name = "marketcheck"

    def __init__(self, model: Model, api_key: Optional[str] = None,
                 endpoint: Optional[str] = None, timeout: int = 25):
        super().__init__(model)
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
        if not (self.model.marketcheck_make and self.model.marketcheck_models):
            log.info(
                "marketcheck : modele '%s' non configure pour Marketcheck",
                self.model.slug,
            )
            return []
        listings: List[Listing] = []
        seen: set[str] = set()
        for mc_model in self.model.marketcheck_models:
            listings.extend(self._fetch_model(mc_model, seen))
        log.info("marketcheck : %d annonces au total", len(listings))
        return listings

    def _fetch_model(self, mc_model: str, seen: set) -> List[Listing]:
        collected: List[Listing] = []
        start = 0
        while start < _MAX_PER_MODEL:
            params = {
                "api_key": self.api_key,
                "make": self.model.marketcheck_make,
                "model": mc_model,
                "car_type": "used",
                "country": "US",
                "rows": _ROWS,
                "start": start,
            }
            try:
                payload = self._get_json(self.endpoint + "?" + urlencode(params))
            except (HTTPError, URLError, OSError, ValueError) as exc:
                log.warning("marketcheck : echec de la requete '%s' (%s)",
                            mc_model, exc)
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
        log.info("marketcheck : '%s' -> %d annonces", mc_model, len(collected))
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

    def _to_listing(self, raw: dict) -> Optional[Listing]:
        if not isinstance(raw, dict):
            return None
        build = raw.get("build") or {}
        year = parse_int(build.get("year"))
        lo_y, hi_y = self.model.year_range
        if not year or not (lo_y <= year <= hi_y):
            return None

        price = parse_int(raw.get("price"))
        lo_p, hi_p = self.model.price_range
        if not price or not (lo_p <= price <= hi_p):
            return None

        mileage = parse_int(raw.get("miles"))
        if mileage is not None and mileage > self.model.max_mileage:
            mileage = None

        trim = build.get("trim") or ""
        model_label = build.get("model") or ""
        variant = self.model.classify_variant(f"{model_label} {trim}")

        dealer = raw.get("dealer") or {}
        location = ", ".join(
            part for part in (dealer.get("city"), dealer.get("state")) if part
        )

        clean = raw.get("carfax_clean_title")
        posted_at = _to_iso_date(raw.get("first_seen_at"))

        media = raw.get("media") if isinstance(raw.get("media"), dict) else {}
        photos = media.get("photo_links")
        image_url = ""
        if isinstance(photos, list) and photos:
            first = photos[0]
            if isinstance(first, str):
                image_url = first
            elif isinstance(first, dict):
                image_url = str(first.get("url") or first.get("href") or "")

        return Listing(
            year=year,
            variant=variant,
            price=price,
            mileage=mileage,
            title=self.model.title_for(year, variant),
            url=raw.get("vdp_url") or "",
            source="marketcheck",
            location=location,
            status="for_sale",
            vin=str(raw.get("vin") or ""),
            image_url=image_url,
            clean_title=clean if isinstance(clean, bool) else None,
            posted_at=posted_at,
        )


def _to_iso_date(value) -> Optional[str]:
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d")
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    return None
