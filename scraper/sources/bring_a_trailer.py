"""Scraper Bring a Trailer - enchères et résultats de ventes.

Bring a Trailer publie des resultats d'encheres detailles (prix reellement
atteints), une reference precieuse pour un investisseur. L'extraction du JSON
embarque est assuree par `HtmlJsonSource`.
"""

from __future__ import annotations

from .html_json import HtmlJsonSource


class BringATrailerSource(HtmlJsonSource):
    name = "bringatrailer.com"
    base_url = "https://bringatrailer.com"
    kind = "auction"
    pages = [
        "https://bringatrailer.com/ferrari/458-italia/",
        "https://bringatrailer.com/ferrari/458-spider/",
        "https://bringatrailer.com/ferrari/458-speciale/",
    ]
