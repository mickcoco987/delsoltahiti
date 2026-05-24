"""Base de scraping pour les sources exposant leurs annonces dans un JSON embarque.

Beaucoup de sites (classic.com, Bring a Trailer, cars.com) rendent leurs pages
avec les donnees vehicule dans un bloc JSON : JSON-LD schema.org, donnees
Next.js `__NEXT_DATA__`, ou autre `<script type="application/json">`.

Cette base telecharge les pages, extrait tous les blocs JSON et les parcourt
recursivement pour en retirer les objets ressemblant a une annonce. Le filtre
de modele (annee, prix, kilometrage, version, titre) est applique a partir
du `Model` courant ; chaque source n'a qu'a fournir la liste des `pages`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Iterable, Iterator, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..models import Listing, extract_vin, parse_int, parse_year
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
    timeout = 25
    kind = "dealer"  # surcharge par les sources d'encheres

    @property
    def pages(self) -> List[str]:
        """Override dans les sous-classes pour lire l'URL adaptee au modele."""
        return []

    def fetch(self) -> List[Listing]:
        pages = self.pages
        if not pages:
            log.info("%s : modele '%s' non configure pour cette source",
                     self.name, self.model.slug)
            return []
        listings: List[Listing] = []
        seen: set[str] = set()
        for url in pages:
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
        has_year = (
            _first(obj, YEAR_KEYS) is not None or parse_year(title) is not None
        )
        has_identity = _first(obj, URL_KEYS) is not None or bool(title)
        return has_price and has_year and has_identity

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        title = str(_first(obj, TITLE_KEYS) or "").strip()
        year = parse_int(_unwrap(_first(obj, YEAR_KEYS))) or parse_year(
            title, self.model.year_range,
        )
        lo_y, hi_y = self.model.year_range
        if not year or not (lo_y <= year <= hi_y):
            return None

        price = _extract_price(obj)
        lo_p, hi_p = self.model.price_range
        if not price or not (lo_p <= price <= hi_p):
            return None

        mileage = parse_int(_unwrap(_first(obj, MILEAGE_KEYS)))
        if mileage is not None and mileage > self.model.max_mileage:
            mileage = None

        url = str(_first(obj, URL_KEYS) or "")
        if url.startswith("/") and self.base_url:
            url = self.base_url + url

        # Filtre anti-bruit : le titre/URL doit mentionner le modele.
        if not self.model.matches_title(f"{title} {url}"):
            return None

        variant = self.model.classify_variant(f"{title} {url}")
        sold_marker = _first(obj, SOLD_KEYS)
        status = "sold" if sold_marker else "for_sale"
        vin = extract_vin(f"{url} {title}", self.model.vin_prefixes)

        return Listing(
            year=year,
            variant=variant,
            price=price,
            mileage=mileage,
            title=title or self.model.title_for(year, variant),
            url=url,
            source=self.name,
            status=status,
            sale_date=str(sold_marker) if sold_marker else None,
            kind=self.kind,
            vin=vin,
        )
