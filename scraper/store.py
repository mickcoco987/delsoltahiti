"""Lecture / ecriture des fichiers de donnees et du bundle du tableau de bord."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List

from .aggregate import build_market
from .models import Listing, utc_now_iso

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LISTINGS_FILE = DATA_DIR / "listings.json"
HISTORY_FILE = DATA_DIR / "history.json"
BUNDLE_FILE = DATA_DIR / "dashboard.js"


def _write_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load_listings() -> List[Listing]:
    if not LISTINGS_FILE.exists():
        return []
    data = json.loads(LISTINGS_FILE.read_text(encoding="utf-8"))
    return [Listing.from_dict(d) for d in data.get("listings", [])]


def load_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    return json.loads(HISTORY_FILE.read_text(encoding="utf-8")).get("points", [])


def append_history(history: list, market: dict) -> list:
    """Ajoute (ou remplace) le point du jour dans l'historique de cote."""
    today = date.today().isoformat()
    overall = market["overall"]
    point = {
        "date": today,
        "overall": {
            "avg_price": overall["avg_price"],
            "median_price": overall["median_price"],
            "count": overall["count"],
        },
        "by_variant": {
            variant: market["by_variant"][variant]["avg_price"]
            for variant in market["by_variant"]
        },
    }
    history = [p for p in history if p.get("date") != today]
    history.append(point)
    history.sort(key=lambda p: p["date"])
    return history


def save(listings: List[Listing], history: list, sources: List[str],
         valuation_method: str = "") -> dict:
    """Ecrit listings.json, history.json et le bundle dashboard.js."""
    DATA_DIR.mkdir(exist_ok=True)
    market = build_market(listings)
    generated_at = utc_now_iso()

    _write_json(
        LISTINGS_FILE,
        {
            "generated_at": generated_at,
            "sources": sources,
            "count": len(listings),
            "listings": [l.to_dict() for l in listings],
        },
    )
    _write_json(HISTORY_FILE, {"points": history})

    bundle = {
        "generated_at": generated_at,
        "sources": sources,
        "valuation": {"method": valuation_method},
        "market": market,
        "history": history,
        "listings": [l.to_dict() for l in listings],
    }
    BUNDLE_FILE.write_text(
        "/* Genere automatiquement par le scraper - ne pas editer a la main. */\n"
        "window.COTE = " + json.dumps(bundle, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    return market
