"""Source RM Sotheby's - maison d'encheres specialisee voitures de collection."""

from __future__ import annotations

from typing import List

from .html_json import HtmlJsonSource


class RmSothebysSource(HtmlJsonSource):
    name = "rmsothebys.com"
    base_url = "https://rmsothebys.com"
    kind = "auction"

    @property
    def pages(self) -> List[str]:
        return list(self.model.rm_sothebys_pages)
