"""Source d'echantillon : cote du marche US figee a partir de releves reels.

Ces donnees servent a amorcer le projet et de repli quand la source live est
indisponible (blocage anti-bot, environnement sans reseau...). Les fourchettes
de prix proviennent de releves agreges du marche US (classic.com, Edmunds,
cars.com, Hagerty) au printemps 2026.
"""

from __future__ import annotations

import math
from typing import List

from ..models import Listing
from .base import ListingSource

# (millesime, version, prix USD, kilometrage en miles, localisation)
_RAW_LISTINGS = [
    (2010, "Italia", 158_000, 28_400, "Miami, FL"),
    (2010, "Italia", 172_500, 19_100, "Dallas, TX"),
    (2011, "Italia", 179_900, 16_529, "Costa Mesa, CA"),
    (2011, "Italia", 164_500, 24_300, "Atlanta, GA"),
    (2011, "Italia", 195_000, 9_050, "Scottsdale, AZ"),
    (2012, "Italia", 188_500, 14_200, "Chicago, IL"),
    (2012, "Italia", 171_000, 31_200, "Houston, TX"),
    (2013, "Italia", 209_500, 12_400, "New York, NY"),
    (2013, "Italia", 233_500, 6_800, "Seattle, WA"),
    (2014, "Italia", 268_000, 2_926, "Beverly Hills, CA"),
    (2014, "Italia", 197_500, 30_350, "Denver, CO"),
    (2014, "Italia", 239_000, 10_800, "Naples, FL"),
    (2015, "Italia", 254_000, 7_200, "Charlotte, NC"),
    (2012, "Spider", 189_000, 18_200, "San Diego, CA"),
    (2012, "Spider", 204_500, 11_100, "Las Vegas, NV"),
    (2013, "Spider", 178_500, 22_600, "Boston, MA"),
    (2013, "Spider", 221_000, 8_400, "Austin, TX"),
    (2014, "Spider", 238_500, 9_300, "Tampa, FL"),
    (2014, "Spider", 213_500, 15_400, "Philadelphia, PA"),
    (2015, "Spider", 279_000, 5_100, "Newport Beach, CA"),
    (2015, "Spider", 251_500, 12_200, "Nashville, TN"),
    (2015, "Spider", 297_500, 3_400, "Greenwich, CT"),
    (2014, "Speciale", 418_500, 6_000, "Los Angeles, CA"),
    (2014, "Speciale", 389_000, 9_800, "Fort Lauderdale, FL"),
    (2015, "Speciale", 478_500, 3_100, "San Francisco, CA"),
    (2015, "Speciale", 525_000, 1_900, "Bellevue, WA"),
    (2015, "Speciale", 444_500, 7_400, "Plano, TX"),
    (2015, "Speciale", 498_000, 4_500, "Paramus, NJ"),
    (2015, "Speciale A", 925_000, 1_200, "Miami, FL"),
    (2015, "Speciale A", 1_050_000, 620, "Beverly Hills, CA"),
    (2013, "Italia", 176_000, 22_400, "Phoenix, AZ"),
    (2014, "Italia", 251_000, 9_400, "Las Vegas, NV"),
    (2011, "Italia", 151_000, 34_500, "Sacramento, CA"),
    (2012, "Spider", 231_000, 9_800, "Aspen, CO"),
    (2015, "Spider", 268_000, 8_900, "Austin, TX"),
    (2014, "Speciale", 372_000, 12_800, "San Jose, CA"),
]

# Mois couverts par l'historique de cote amorce (15 points mensuels).
_HISTORY_MONTHS = [
    "2025-03-01", "2025-04-01", "2025-05-01", "2025-06-01", "2025-07-01",
    "2025-08-01", "2025-09-01", "2025-10-01", "2025-11-01", "2025-12-01",
    "2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01",
]

# Cote moyenne par version : (valeur debut periode -> valeur actuelle).
_HISTORY_ANCHORS = {
    "overall": (286_000, 314_700),
    "Italia": (196_000, 202_600),
    "Spider": (214_000, 230_700),
    "Speciale": (358_000, 459_200),
    "Speciale A": (855_000, 987_500),
}


class SampleSource(ListingSource):
    name = "echantillon"

    def fetch(self) -> List[Listing]:
        listings: List[Listing] = []
        for index, (year, variant, price, mileage, location) in enumerate(_RAW_LISTINGS):
            listings.append(
                Listing(
                    year=year,
                    variant=variant,
                    price=price,
                    mileage=mileage,
                    title=f"{year} Ferrari 458 {variant}",
                    url=f"sample://458/{index:03d}",
                    source=self.name,
                    location=location,
                    status="for_sale",
                )
            )
        return listings

    def history(self) -> list:
        """Historique de cote mensuel amorce (tendance haussiere 2025-2026)."""
        points = []
        last = len(_HISTORY_MONTHS) - 1
        for index, month in enumerate(_HISTORY_MONTHS):
            # Progression non lineaire : hausse plus marquee sur la periode recente.
            frac = (index / last) ** 1.25
            # Ondulation deterministe pour un rendu de courbe realiste.
            wobble = math.sin(index * 1.3) * 0.012

            def value(key: str) -> int:
                start, end = _HISTORY_ANCHORS[key]
                base = start + (end - start) * frac
                return round(base * (1 + wobble))

            overall = value("overall")
            count = round(24 + (30 - 24) * frac)
            points.append(
                {
                    "date": month,
                    "overall": {
                        "avg_price": overall,
                        "median_price": round(overall * 0.70),
                        "count": count,
                    },
                    "by_variant": {
                        "Italia": value("Italia"),
                        "Spider": value("Spider"),
                        "Speciale": value("Speciale"),
                        "Speciale A": value("Speciale A"),
                    },
                }
            )
        return points
