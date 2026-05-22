"""Source d'echantillon : cote du marche US figee a partir de releves reels.

Ces donnees servent a amorcer le projet et de repli quand la source live est
indisponible (blocage anti-bot, environnement sans reseau...). Les fourchettes
de prix proviennent de releves agreges du marche US (classic.com, Edmunds,
cars.com, Hagerty) au printemps 2026.

Cette source ne fournit que des annonces : l'historique de cote se construit
uniquement a partir de mesures reelles, au fil des executions du scraper.
"""

from __future__ import annotations

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
