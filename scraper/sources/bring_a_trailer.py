"""Scraper Bring a Trailer - encheres et resultats de ventes.

BaT publie des resultats d'encheres detailles (prix reellement atteints) :
reference pour un investisseur. La page de recherche
/auctions/?search=Ferrari+458 ne contient pas toujours les annonces dans un
bloc JSON exploitable directement ; ce scraper fait donc deux passes :

1) Telecharge la page de recherche, tente d'abord l'extraction JSON
   classique (HtmlJsonSource) ;
2) Si rien n'est trouve, recupere les liens vers les pages d'annonces
   individuelles via regex (`/listing/<slug>/` contenant "ferrari" et
   "458") et applique l'extraction JSON sur chacune (les pages d'annonces
   contiennent typiquement du JSON-LD Vehicle).
"""

from __future__ import annotations

import logging
import re
from typing import Iterator, List, Optional
from urllib.error import HTTPError, URLError

from ..models import Listing
from .html_json import HtmlJsonSource

log = logging.getLogger(__name__)

# Lien vers une annonce BaT individuelle. Le slug contient ferrari+458 pour
# eliminer les liens vers d'autres modeles potentiellement presents sur la
# meme page (recommandations, "vous aimerez aussi"...).
_LISTING_PATH_RE = re.compile(r'/listing/([a-z0-9][a-z0-9\-]+)/', re.IGNORECASE)
_MAX_LISTINGS = 40   # plafond defensif (chaque page individuelle = un fetch)


class BringATrailerSource(HtmlJsonSource):
    name = "bringatrailer.com"
    base_url = "https://bringatrailer.com"
    kind = "auction"
    pages = [
        "https://bringatrailer.com/auctions/?search=Ferrari+458",
    ]

    def fetch(self) -> List[Listing]:
        listings: List[Listing] = []
        seen_ids: set[str] = set()

        for search_url in self.pages:
            try:
                search_html = self._get(search_url)
            except (HTTPError, URLError, OSError) as exc:
                log.warning("%s : echec sur %s (%s)", self.name, search_url, exc)
                continue

            # Passe 1 : extraction JSON directement sur la page de recherche.
            for listing in self._harvest(search_html):
                if listing.id not in seen_ids:
                    seen_ids.add(listing.id)
                    listings.append(listing)

            if listings:
                continue  # la passe 1 a suffi

            # Passe 2 : suivre les liens d'annonces individuelles.
            slugs = {
                s for s in _LISTING_PATH_RE.findall(search_html)
                if "ferrari" in s.lower() and "458" in s.lower()
            }
            log.info(
                "%s : %s -> %d annonces, fetch individuel des pages",
                self.name, search_url, len(slugs),
            )
            for slug in sorted(slugs)[:_MAX_LISTINGS]:
                full = f"{self.base_url}/listing/{slug}/"
                try:
                    page_html = self._get(full)
                except (HTTPError, URLError, OSError) as exc:
                    log.warning("%s : echec sur %s (%s)", self.name, full, exc)
                    continue
                added_before = len(listings)
                for listing in self._harvest(page_html, fallback_url=full):
                    if listing.id not in seen_ids:
                        seen_ids.add(listing.id)
                        listings.append(listing)
                        break   # un listing par page d'annonce suffit
                if len(listings) == added_before:
                    log.info("%s : aucune annonce extraite de %s", self.name, full)

        log.info("%s : %d annonces au total", self.name, len(listings))
        return listings

    def _harvest(self, html: str, fallback_url: str = "") -> Iterator[Listing]:
        for blob in self._iter_json_blobs(html):
            for raw in self._find_listing_objects(blob):
                listing = self._to_listing(raw)
                if not listing:
                    continue
                if fallback_url and not listing.url.startswith("http"):
                    listing.url = fallback_url
                    listing.id = listing._compute_id()
                yield listing

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        listing = super()._to_listing(obj)
        if listing and "458" not in (listing.title + " " + listing.url).lower():
            return None
        return listing
