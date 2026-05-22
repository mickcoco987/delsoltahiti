"""Source RM Sotheby's - maison d'encheres specialisee voitures de collection.

Scraping best-effort de la page de resultats. Le site est en Next.js, donc
les donnees sont typiquement dans `__NEXT_DATA__` qu'HtmlJsonSource sait lire.
Filtre 458 applique sur le titre.

URL alternative pour debug : `https://w3.rmsothebys.com/results/`.
"""

from __future__ import annotations

from typing import Optional

from ..models import Listing
from .html_json import HtmlJsonSource


class RmSothebysSource(HtmlJsonSource):
    name = "rmsothebys.com"
    base_url = "https://rmsothebys.com"
    kind = "auction"
    pages = [
        "https://rmsothebys.com/results/",
    ]

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        listing = super()._to_listing(obj)
        if listing and "458" not in (listing.title + " " + listing.url).lower():
            return None
        return listing
