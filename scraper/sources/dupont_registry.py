"""Source DuPont Registry Live - encheres automobiles live US.

Plate-forme d'encheres live de DuPont Registry. Scraping best-effort : le site
applique une protection anti-bot, le scraper peut renvoyer 0 annonce. La page
live sert d'entree, le filtre 458 est applique sur le titre.
"""

from __future__ import annotations

from typing import Optional

from ..models import Listing
from .html_json import HtmlJsonSource


class DupontRegistryLiveSource(HtmlJsonSource):
    name = "live.dupontregistry.com"
    base_url = "https://live.dupontregistry.com"
    kind = "auction"
    pages = [
        "https://live.dupontregistry.com/listings/live/filter:sort=ending_soon",
    ]

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        listing = super()._to_listing(obj)
        if listing and "458" not in (listing.title + " " + listing.url).lower():
            return None
        return listing
