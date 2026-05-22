"""Base de scraping pour les sources exposant leurs annonces dans un JSON embarque.

Beaucoup de sites (classic.com, Bring a Trailer, cars.com) rendent leurs pages
avec les donnees vehicule dans un bloc JSON : JSON-LD schema.org, donnees
Next.js `__NEXT_DATA__`, ou autre `<script type="application/json">`.

Cette base telecharge les pages, extrait tous les blocs JSON et les parcourt
recursivement pour en retirer les objets ressemblant a une annonce. Tant que
les donnees restent dans un JSON de la page, le scraper resiste aux
changements de mise en page. Une sous-classe n'a qu'a definir `name`,
`base_url` et `pages`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Iterable, Iterator, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..models import Listing, classify_variant, parse_int, parse_year
from .base import ListingSource

log = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PRICE_KEYS = (
    "price", "sold_price", "soldPrice", "sale_price", "salePrice",
    "current_price", "currentPrice", "asking_price", "amount", "high_bid",
)
MILEAGE_KEYS = ("mileage", "miles", "odometer", "mileageFromOdometer", "kms")
YEAR_KEYS = (
    "year", "model_year", "modelYear", "vehicleModelDate", "modelDate",
    "productionDate",
)
TITLE_KEYS = ("title", "name", "headline", "full_name", "fullName", "label")
URL_KEYS = ("url", "permalink", "link", "slug", "href", "path")
SOLD_KEYS = ("sold_date", "soldDate", "sale_date", "saleDate")

# Bornes de plausibilite pour ecarter le bruit (accessoires, autres modeles).
MIN_PRICE = 40_000
MAX_PRICE = 3_000_000
MAX_MILEAGE = 200_000


def _first(obj: dict, keys: Iterable[str]):
    for key in keys:
        if key in obj and obj[key] not in (None, "", [], {}):
            return obj[key]
    return None


def _unwrap(value):
    """Deplie une valeur schema.org QuantitativeValue {value: x, unitCode: ...}."""
    if isinstance(value, dict):
        return value.get("value", value.get("amount"))
    if isinstance(value, list) and value:
        return value[0]
    return value


def _extract_price(obj: dict) -> Optional[int]:
    direct = parse_int(_unwrap(_first(obj, PRICE_KEYS)))
    if direct:
        return direct
    offers = obj.get("offers")
    candidates = offers if isinstance(offers, list) else [offers]
    for offer in candidates:
        if isinstance(offer, dict):
            price = parse_int(_unwrap(_first(offer, PRICE_KEYS)))
            if not price and isinstance(offer.get("priceSpecification"), dict):
                price = parse_int(
                    _unwrap(_first(offer["priceSpecification"], PRICE_KEYS))
                )
            if price:
                return price
    return None


class HtmlJsonSource(ListingSource):
    """Source generique : pages HTML contenant les annonces dans un JSON."""

    name = "html-json"
    base_url = ""
    pages: List[str] = []
    timeout = 25

    def fetch(self) -> List[Listing]:
        listings: List[Listing] = []
        seen: set[str] = set()
        for url in self.pages:
            try:
                html = self._get(url)
            except (HTTPError, URLError, OSError) as exc:
                log.warning("%s : echec du telechargement de %s (%s)",
                            self.name, url, exc)
                continue
            found = 0
            for blob in self._iter_json_blobs(html):
                for raw in self._find_listing_objects(blob):
                    listing = self._to_listing(raw)
                    if listing and listing.id not in seen:
                        seen.add(listing.id)
                        listings.append(listing)
                        found += 1
            log.info("%s : %s -> %d annonces", self.name, url, found)
        log.info("%s : %d annonces au total", self.name, len(listings))
        return listings

    def _get(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")

    @staticmethod
    def _iter_json_blobs(html: str) -> Iterator:
        patterns = [
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
                try:
                    yield json.loads(match.group(1).strip())
                except (json.JSONDecodeError, ValueError):
                    continue

    @classmethod
    def _find_listing_objects(cls, node, depth: int = 0) -> Iterator[dict]:
        if depth > 14:
            return
        if isinstance(node, dict):
            if cls._looks_like_listing(node):
                yield node
            for value in node.values():
                yield from cls._find_listing_objects(value, depth + 1)
        elif isinstance(node, list):
            for value in node:
                yield from cls._find_listing_objects(value, depth + 1)

    @staticmethod
    def _looks_like_listing(obj: dict) -> bool:
        has_price = _extract_price(obj) is not None
        title = str(_first(obj, TITLE_KEYS) or "")
        has_year = _first(obj, YEAR_KEYS) is not None or parse_year(title) is not None
        has_identity = _first(obj, URL_KEYS) is not None or bool(title)
        return has_price and has_year and has_identity

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        title = str(_first(obj, TITLE_KEYS) or "").strip()
        year = parse_int(_unwrap(_first(obj, YEAR_KEYS))) or parse_year(title)
        if not year or not (2009 <= year <= 2016):
            return None

        price = _extract_price(obj)
        if not price or not (MIN_PRICE <= price <= MAX_PRICE):
            return None

        mileage = parse_int(_unwrap(_first(obj, MILEAGE_KEYS)))
        if mileage is not None and mileage > MAX_MILEAGE:
            mileage = None

        url = str(_first(obj, URL_KEYS) or "")
        if url.startswith("/") and self.base_url:
            url = self.base_url + url

        variant = classify_variant(f"{title} {url}")
        sold_marker = _first(obj, SOLD_KEYS)
        status = "sold" if sold_marker else "for_sale"

        return Listing(
            year=year,
            variant=variant,
            price=price,
            mileage=mileage,
            title=title or f"{year} Ferrari 458 {variant}",
            url=url,
            source=self.name,
            status=status,
            sale_date=str(sold_marker) if sold_marker else None,
        )
