"""Source DuPont Registry Live - encheres automobiles live US (best-effort)."""

from __future__ import annotations

from typing import List

from .html_json import HtmlJsonSource


class DupontRegistryLiveSource(HtmlJsonSource):
    name = "live.dupontregistry.com"
    base_url = "https://live.dupontregistry.com"
    kind = "auction"

    @property
    def pages(self) -> List[str]:
        return list(self.model.dupont_live_pages)
