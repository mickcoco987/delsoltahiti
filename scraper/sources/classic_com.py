"""Scraper classic.com - agregateur de cote du marche automobile US."""

from __future__ import annotations

from typing import List

from .html_json import HtmlJsonSource


class ClassicComSource(HtmlJsonSource):
    name = "classic.com"
    base_url = "https://www.classic.com"
    kind = "dealer"

    @property
    def pages(self) -> List[str]:
        return list(self.model.classic_pages)
