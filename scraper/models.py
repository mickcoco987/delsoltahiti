"""Modeles de donnees du suivi de cote (multi-modeles)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional, Sequence


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


def parse_year(text, year_range: Sequence[int] = (2000, 2030)) -> Optional[int]:
    """Trouve un millesime plausible (dans la plage donnee) dans un texte libre."""
    text = str(text or "")
    lo, hi = year_range[0], year_range[1]
    for match in re.finditer(r"\b(19[7-9]\d|20[0-4]\d)\b", text):
        year = int(match.group(1))
        if lo <= year <= hi:
            return year
    return None


def extract_vin(text: str, prefixes: Sequence[str] = ()) -> str:
    """Extrait un VIN d'un texte libre, en testant chaque prefixe constructeur.

    Renvoie le VIN trouve (17 caracteres, MAJ), sinon chaine vide. Les
    caracteres I, O, Q sont interdits dans un VIN par la norme.
    """
    if not text or not prefixes:
        return ""
    body = str(text)
    for prefix in prefixes:
        pattern = re.compile(
            re.escape(prefix) + r"[A-HJ-NPR-Z0-9]{14}", re.IGNORECASE,
        )
        match = pattern.search(body)
        if match:
            return match.group(0).upper()
    return ""


@dataclass
class Listing:
    """Une annonce relevee sur le marche, agnostique du modele."""

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
    posted_at: Optional[str] = None  # date de mise en ligne (YYYY-MM-DD)
    kind: str = "dealer"  # dealer | auction
    scraped_at: str = field(default_factory=utc_now_iso)
    id: str = ""
    vin: str = ""
    image_url: str = ""
    clean_title: Optional[bool] = None
    # Champs calcules par le moteur de valuation (voir scraper/valuation.py).
    estimated_value: Optional[int] = None
    deal_pct: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = self._compute_id()
        if self.vin:
            self.vin = self.vin.strip().upper()

    def _compute_id(self) -> str:
        basis = self.url or (
            f"{self.source}|{self.title}|{self.year}|{self.price}|{self.mileage}"
        )
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Listing":
        fields = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in fields})
