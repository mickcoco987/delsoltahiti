"""Modeles de donnees du suivi de cote Ferrari 458 Italia."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

# Versions reconnues du modele 458 sur le marche US (millesimes 2010-2015).
VARIANTS = ["Italia", "Spider", "Speciale", "Speciale A"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_int(value) -> Optional[int]:
    """Extrait un entier d'une valeur heterogene (str, float, dict {value: x})."""
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("value", value.get("amount"))
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[^\d]", "", str(value).split(".")[0])
    return int(digits) if digits else None


def parse_year(text) -> Optional[int]:
    """Trouve un millesime plausible (2009-2016) dans un texte libre."""
    match = re.search(r"\b(20[01]\d)\b", str(text or ""))
    if match:
        year = int(match.group(1))
        if 2009 <= year <= 2016:
            return year
    return None


def classify_variant(text: str) -> str:
    """Detecte la version a partir d'un titre/URL d'annonce."""
    t = (text or "").lower()
    if "speciale a" in t or "aperta" in t:
        return "Speciale A"
    if "speciale" in t:
        return "Speciale"
    if "spider" in t or "spyder" in t:
        return "Spider"
    return "Italia"


@dataclass
class Listing:
    """Une annonce de Ferrari 458 relevee sur le marche."""

    year: int
    variant: str
    price: Optional[int]
    mileage: Optional[int] = None
    title: str = ""
    url: str = ""
    source: str = ""
    location: str = ""
    status: str = "for_sale"  # for_sale | sold
    sale_date: Optional[str] = None
    scraped_at: str = field(default_factory=utc_now_iso)
    id: str = ""

    def __post_init__(self) -> None:
        if self.variant not in VARIANTS:
            self.variant = classify_variant(self.variant or self.title)
        if not self.title:
            self.title = f"{self.year} Ferrari 458 {self.variant}"
        if not self.id:
            self.id = self._compute_id()

    def _compute_id(self) -> str:
        basis = self.url or f"{self.source}|{self.title}|{self.year}|{self.price}|{self.mileage}"
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Listing":
        fields = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in fields})
