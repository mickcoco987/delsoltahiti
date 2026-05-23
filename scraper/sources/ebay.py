"""Source eBay Motors - encheres et Buy-It-Now via l'API officielle Browse.

L'API Browse d'eBay est gratuite avec une app developpeur (oauth Client
Credentials). Elle necessite EBAY_CLIENT_ID et EBAY_CLIENT_SECRET dans
l'environnement ; sans, la source est ignoree sans erreur.

DEPLOIEMENT
-----------
1. Cree une app gratuite sur https://developer.ebay.com/my/keys
   - Utilise les credentials "Production" (App ID = Client ID, Cert ID =
     Client Secret).
   - Demande l'exemption "Marketplace Account Deletion" (motif : application
     consomme uniquement l'API Browse publique, ne stocke aucune donnee
     utilisateur).
2. Expose les deux comme secrets GitHub Actions :
     EBAY_CLIENT_ID
     EBAY_CLIENT_SECRET
   Le workflow les injecte automatiquement.

Strategie : la recherche `item_summary/search` donne le titre/prix/URL mais
n'expose ni kilometrage ni VIN. On enrichit chaque annonce par un appel a
`/v1/item/{itemId}` qui retourne les `localizedAspects` (specifications
detaillees du vehicule) -> on y trouve typiquement "Mileage" et "VIN".
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import Listing, classify_variant, parse_int, parse_year
from .base import ListingSource

log = logging.getLogger(__name__)

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
BROWSE_ITEM_URL = "https://api.ebay.com/buy/browse/v1/item"
SCOPE = "https://api.ebay.com/oauth/api_scope"
MARKETPLACE = "EBAY_US"
CATEGORY_CARS_TRUCKS = "6001"

MIN_PRICE = 40_000
MAX_PRICE = 3_000_000
MAX_MILEAGE = 200_000
_MILEAGE_RE = re.compile(
    r"(\d{1,3}(?:[,\s]\d{3})*|\d{4,6})\s*(?:miles?|mi)\b", re.IGNORECASE,
)


class EbayMotorsSource(ListingSource):
    name = "ebay"

    def __init__(self, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None, timeout: int = 25):
        self.client_id = client_id or os.environ.get("EBAY_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("EBAY_CLIENT_SECRET", "")
        self.timeout = timeout

    def fetch(self) -> List[Listing]:
        if not (self.client_id and self.client_secret):
            log.warning(
                "ebay : EBAY_CLIENT_ID / EBAY_CLIENT_SECRET absents, source "
                "ignoree. Cree une app sur developer.ebay.com/my/keys."
            )
            return []

        try:
            token = self._get_token()
        except (HTTPError, URLError, OSError, ValueError) as exc:
            log.warning("ebay : echec OAuth (%s)", exc)
            return []
        if not token:
            return []

        try:
            payload = self._search(token)
        except (HTTPError, URLError, OSError, ValueError) as exc:
            log.warning("ebay : echec de la recherche (%s)", exc)
            return []

        listings: List[Listing] = []
        seen: set[str] = set()
        enriched = 0
        for raw in payload.get("itemSummaries") or []:
            detail = self._fetch_item_detail(raw.get("itemId"), token)
            if detail:
                enriched += 1
            listing = self._to_listing(raw, detail)
            if listing and listing.id not in seen:
                seen.add(listing.id)
                listings.append(listing)
        log.info("ebay : %d annonces (%d enrichies via /item)",
                 len(listings), enriched)
        return listings

    def _get_token(self) -> str:
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("ascii"),
        ).decode("ascii")
        body = urlencode({
            "grant_type": "client_credentials",
            "scope": SCOPE,
        }).encode("ascii")
        request = Request(OAUTH_URL, data=body, headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        })
        with urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
        return data.get("access_token", "")

    def _search(self, token: str) -> dict:
        params = {
            "q": "Ferrari 458",
            "category_ids": CATEGORY_CARS_TRUCKS,
            "filter": "buyingOptions:{AUCTION|AUCTION_WITH_BIN}",
            "limit": "200",
        }
        url = f"{BROWSE_SEARCH_URL}?{urlencode(params)}"
        request = Request(url, headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
            "Accept": "application/json",
        })
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))

    def _fetch_item_detail(self, item_id: Optional[str], token: str) -> dict:
        """Recupere les specifications detaillees d'un item (mileage, VIN...).

        Renvoie un dict vide en cas d'erreur ; la source continue avec les
        donnees du resume.
        """
        if not item_id:
            return {}
        url = f"{BROWSE_ITEM_URL}/{item_id}"
        request = Request(url, headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
            "Accept": "application/json",
        })
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except (HTTPError, URLError, OSError, ValueError) as exc:
            log.warning("ebay : echec /item/%s (%s)", item_id, exc)
            return {}

    @staticmethod
    def _to_listing(raw: dict, detail: Optional[dict] = None) -> Optional[Listing]:
        if not isinstance(raw, dict):
            return None
        title = str(raw.get("title") or "")
        if "458" not in title:
            return None
        year = parse_year(title)
        if not year or not (2009 <= year <= 2016):
            return None

        price = parse_int((raw.get("price") or {}).get("value"))
        if not price or not (MIN_PRICE <= price <= MAX_PRICE):
            return None

        # Kilometrage et VIN : prio aux itemSpecifics (localizedAspects) du
        # detail item, fallback sur le titre pour le mileage.
        mileage = None
        vin = ""
        for aspect in ((detail or {}).get("localizedAspects") or []):
            name = (aspect.get("name") or "").lower()
            value = str(aspect.get("value") or "").strip()
            if not value:
                continue
            if not mileage and ("mileage" in name or "odometer" in name):
                m = parse_int(value)
                if m and m <= MAX_MILEAGE:
                    mileage = m
            elif not vin and (name == "vin" or "vehicle identification" in name):
                vin = value.upper()
        if not mileage:
            match = _MILEAGE_RE.search(title)
            if match:
                m = parse_int(match.group(1))
                if m and m <= MAX_MILEAGE:
                    mileage = m

        location = (raw.get("itemLocation") or {}).get("country") or ""
        return Listing(
            year=year,
            variant=classify_variant(title),
            price=price,
            mileage=mileage,
            title=title[:160],
            url=str(raw.get("itemWebUrl") or ""),
            source="ebay",
            location=location,
            status="for_sale",
            vin=vin,
            kind="auction",
        )
