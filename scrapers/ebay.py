from typing import List

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper
from models import Listing, Condition


class EbayScraper(BaseScraper):
    SOURCE_NAME = "eBay.pt"
    BASE_URL    = "https://www.ebay.pt"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def scrape(self, query: str) -> List[Listing]:
        q = query.replace(" ", "+")
        # _sop=15 = lowest price + shipping first;  LH_ItemCondition filters used items
        url = (
            f"{self.BASE_URL}/sch/i.html?_nkw={q}"
            "&_sacat=0&_sop=15&LH_ItemCondition=2000%7C2500%7C3000%7C7000"
        )
        listings: List[Listing] = []

        try:
            resp = requests.get(url, headers=self._HEADERS, timeout=20)
            resp.raise_for_status()
            soup  = BeautifulSoup(resp.text, "lxml")
            items = soup.select("li.s-item")

            for item in items[: self.max_results + 5]:   # +5 to skip header dummy items
                lst = self._parse_item(item)
                if lst:
                    listings.append(lst)
                if len(listings) >= self.max_results:
                    break

        except Exception as exc:
            print(f"[eBay] error: {exc}")

        return listings

    def _parse_item(self, item) -> Listing | None:
        try:
            title_el = item.select_one(".s-item__title")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            # Skip eBay's injected "Shop on eBay" header card
            if "SHOP ON EBAY" in title.upper() or not title:
                return None

            link_el = item.select_one(".s-item__link")
            url     = link_el["href"] if link_el and link_el.get("href") else ""
            # Strip tracking params for cleanliness (keep base URL)
            url = url.split("?")[0] if url else ""

            price_el = item.select_one(".s-item__price")
            price    = self._parse_price(price_el.get_text() if price_el else "0")

            loc_el   = item.select_one(".s-item__location, .s-item__itemLocation")
            location = loc_el.get_text(strip=True).replace("de ", "") if loc_el else "Internacional"

            cond_el       = item.select_one(".SECONDARY_INFO, [class*='condition']")
            condition_str = cond_el.get_text(strip=True) if cond_el else ""
            condition     = self._parse_condition(condition_str)

            img_el    = item.select_one("img")
            image_url = (
                img_el.get("src") or img_el.get("data-src")
            ) if img_el else None

            # Filter out "Buy It Now" price ranges  (contains "a" between two prices)
            if " a " in (price_el.get_text() if price_el else "") and price <= 0:
                return None

            return Listing(
                title=title,
                price=price,
                condition=condition,
                location=location,
                url=url,
                source=self.SOURCE_NAME,
                image_url=image_url,
                raw_condition=condition_str,
            )
        except Exception as exc:
            print(f"[eBay] item parse error: {exc}")
            return None
