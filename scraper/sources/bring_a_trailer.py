"""Scraper Bring a Trailer - encheres et resultats de ventes.

Bring a Trailer publie des resultats d'encheres detailles (prix reellement
atteints), une reference precieuse pour un investisseur. L'extraction du JSON
embarque est assuree par `HtmlJsonSource`.

URL utilisee : la recherche d'encheres actives filtree sur "Ferrari 458". Le
filtre 458 sur le titre evite les voitures voisines qui pourraient apparaitre
dans des sections "vous aimerez aussi".
"""

from __future__ import annotations

from typing import Optional

from ..models import Listing
from .html_json import HtmlJsonSource


class BringATrailerSource(HtmlJsonSource):
    name = "bringatrailer.com"
    base_url = "https://bringatrailer.com"
    kind = "auction"
    pages = [
        "https://bringatrailer.com/auctions/?search=Ferrari+458",
    ]

    def _to_listing(self, obj: dict) -> Optional[Listing]:
        listing = super()._to_listing(obj)
        if listing and "458" not in (listing.title + " " + listing.url).lower():
            return None
        return listing
