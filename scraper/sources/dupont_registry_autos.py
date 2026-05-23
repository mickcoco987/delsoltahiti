"""Source DuPont Registry (site principal autos) - classifieds exotiques.

Distinct du sous-domaine `live.dupontregistry.com` (qui gere les encheres
live, deja branche dans dupont_registry.py). Ici on cible le site principal
qui agrege des classifieds de vendeurs et concessionnaires haut de gamme.
Best-effort scraping.
"""

from __future__ import annotations

from typing import Optional

from ..models import Listing
from .html_json import HtmlJsonSource


class DupontRegistryAutosSource(HtmlJsonSource):
    name = "dupontregistry.com"
    base_url = "https://www.dupontregistry.com"
    kind = "dealer"
    pages = [
        "https://www.dupontregistry.com/autos/results/ferrari/458-italia",
    ]

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        listing = super()._to_listing(obj)
        if listing and "458" not in (listing.title + " " + listing.url).lower():
            return None
        return listing
