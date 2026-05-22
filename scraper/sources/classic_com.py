"""Scraper classic.com - agregateur de cote du marche automobile US.

classic.com suit specifiquement la cote (annonces + ventes) modele par modele,
ce qui en fait une source pertinente pour le suivi de valeur d'une Ferrari 458.
L'extraction du JSON embarque est assuree par `HtmlJsonSource`.
"""

from __future__ import annotations

from .html_json import HtmlJsonSource


class ClassicComSource(HtmlJsonSource):
    name = "classic.com"
    base_url = "https://www.classic.com"
    pages = [
        "https://www.classic.com/m/ferrari/458/coupe/",
        "https://www.classic.com/m/ferrari/458/spider/",
        "https://www.classic.com/m/ferrari/458/speciale/",
    ]
