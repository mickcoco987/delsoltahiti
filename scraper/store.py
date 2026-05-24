"""Lecture / ecriture des fichiers de donnees et des bundles du tableau de bord.

Donnees partitionnees par modele : `data/<slug>/{listings,history,dashboard}.json|.js`.
Un fichier `data/catalog.js` agrege la metadata de tous les modeles pour le
selecteur du tableau de bord.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

from .aggregate import build_market
from .catalog import Model
from .models import Listing, utc_now_iso

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CATALOG_BUNDLE = DATA_DIR / "catalog.js"


def model_dir(model: Model) -> Path:
    return DATA_DIR / model.slug


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load_listings(model: Model) -> List[Listing]:
    path = model_dir(model) / "listings.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Listing.from_dict(d) for d in data.get("listings", [])]


def load_history(model: Model) -> list:
    path = model_dir(model) / "history.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("points", [])


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


def save(model: Model, listings: List[Listing], history: list,
         sources: List[str], valuation: Optional[dict] = None) -> dict:
    """Ecrit listings.json, history.json et le bundle dashboard.js pour ce modele."""
    md = model_dir(model)
    md.mkdir(parents=True, exist_ok=True)
    market = build_market(listings, model)
    generated_at = utc_now_iso()

    model_meta = {
        "slug": model.slug,
        "brand": model.brand,
        "name": model.name,
        "short_name": model.short_name,
        "variants": list(model.variants),
        "year_range": list(model.year_range),
        "investment": {
            "verdict": model.investment_verdict,
            "class": model.investment_class,
            "summary": model.investment_summary,
            "focus": model.investment_focus,
            "risk": model.investment_risk,
        },
    }

    _write_json(md / "listings.json", {
        "model": model_meta,
        "generated_at": generated_at,
        "sources": sources,
        "count": len(listings),
        "listings": [l.to_dict() for l in listings],
    })
    _write_json(md / "history.json", {
        "model": model.slug,
        "points": history,
    })

    bundle = {
        "model": model_meta,
        "generated_at": generated_at,
        "sources": sources,
        "valuation": valuation or {},
        "market": market,
        "history": history,
        "listings": [l.to_dict() for l in listings],
    }
    (md / "dashboard.js").write_text(
        "/* Genere automatiquement par le scraper - ne pas editer a la main. */\n"
        "window.COTE = " + json.dumps(bundle, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    return market


def write_catalog(models: Sequence[Model]) -> None:
    """Ecrit data/catalog.js : metadata de tous les modeles pour le selecteur."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for m in models:
        bundle = model_dir(m) / "dashboard.js"
        listings = model_dir(m) / "listings.json"
        entry = {
            "slug": m.slug,
            "brand": m.brand,
            "name": m.name,
            "short_name": m.short_name,
            "variants": list(m.variants),
            "year_range": list(m.year_range),
            "has_data": bundle.exists(),
            "investment": {
                "verdict": m.investment_verdict,
                "class": m.investment_class,
            },
        }
        if listings.exists():
            try:
                data = json.loads(listings.read_text(encoding="utf-8"))
                entry["count"] = data.get("count", 0)
                entry["generated_at"] = data.get("generated_at")
            except (json.JSONDecodeError, OSError):
                pass
        entries.append(entry)
    payload = {"models": entries}
    CATALOG_BUNDLE.write_text(
        "/* Genere automatiquement - ne pas editer a la main. */\n"
        "window.COTE_CATALOG = " + json.dumps(
            payload, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
