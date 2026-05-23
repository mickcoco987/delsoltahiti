"""Source Hemmings - classifieds collection et exotiques US.

Hemmings publie des classifieds depuis 1954 (collection, sport, exotiques) :
historiquement plus server-rendered que les concurrents, le scraping JSON
peut donc passer. Best-effort comme tous les scrapers — anti-bot toujours
possible.
"""

from __future__ import annotations

from typing import Optional

from ..models import Listing
from .html_json import HtmlJsonSource


class HemmingsSource(HtmlJsonSource):
    name = "hemmings.com"
    base_url = "https://www.hemmings.com"
    kind = "dealer"
    pages = [
        "https://www.hemmings.com/classifieds/cars-for-sale/ferrari/458-italia",
    ]

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        listing = super()._to_listing(obj)
        if listing and "458" not in (listing.title + " " + listing.url).lower():
            return None
        return listing
