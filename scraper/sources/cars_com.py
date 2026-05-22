"""Scraper cars.com - annonces de vehicules a vendre aux Etats-Unis.

cars.com agrege les annonces de concessionnaires et de particuliers sur le
marche US. L'extraction du JSON embarque est assuree par `HtmlJsonSource`.
"""

from __future__ import annotations

from .html_json import HtmlJsonSource


class CarsComSource(HtmlJsonSource):
    name = "cars.com"
    base_url = "https://www.cars.com"
    pages = [
        "https://www.cars.com/shopping/ferrari-458_italia/",
        "https://www.cars.com/shopping/ferrari-458_spider/",
    ]
