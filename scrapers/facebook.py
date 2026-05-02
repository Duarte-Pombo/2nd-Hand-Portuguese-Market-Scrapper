import time
from typing import List
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .base import BaseScraper
from models import Listing, Condition


class FacebookScraper(BaseScraper):
    SOURCE_NAME = "Facebook Marketplace"
    BASE_URL    = "https://www.facebook.com"

    def __init__(
        self,
        email:       str,
        password:    str,
        max_results: int  = 30,
        headless:    bool = True,
    ):
        super().__init__(max_results, headless)
        self.email    = email
        self.password = password

    def scrape(self, query: str) -> List[Listing]:
        if not self.email or not self.password:
            print("[Facebook] No credentials provided — skipping.")
            return []

        q        = query.replace(" ", "%20")
        mkt_url  = (
            f"{self.BASE_URL}/marketplace/porto/search/"
            f"?query={q}&exact=false&radius=80"     # 80 km radius around Porto
        )
        listings: List[Listing] = []

        try:
            with sync_playwright() as p:
                browser = self._new_browser(p)
                ctx     = self._new_context(browser)
                page    = ctx.new_page()

                if not self._login(page):
                    print("[Facebook] Login failed. Check your credentials.")
                    browser.close()
                    return []

                page.goto(mkt_url, timeout=30_000, wait_until="domcontentloaded")
                page.wait_for_timeout(4_000)

                # Scroll to trigger lazy-loading
                for _ in range(4):
                    page.keyboard.press("End")
                    page.wait_for_timeout(1_500)

                # Facebook's marketplace items are anchor tags pointing to /marketplace/item/
                cards = page.query_selector_all('a[href*="/marketplace/item/"]')

                seen_urls: set[str] = set()
                for card in cards:
                    if len(listings) >= self.max_results:
                        break
                    lst = self._parse_card(card)
                    if lst and lst.url not in seen_urls:
                        seen_urls.add(lst.url)
                        listings.append(lst)

                browser.close()

        except Exception as exc:
            print(f"[Facebook] error: {exc}")

        return listings

    # ------------------------------------------------------------------ #

    def _login(self, page) -> bool:
        try:
            page.goto(f"{self.BASE_URL}/login", timeout=20_000)
            page.wait_for_selector("#email", timeout=10_000)

            page.fill("#email", self.email)
            page.fill("#pass",  self.password)
            page.click('[name="login"]')

            page.wait_for_load_state("networkidle", timeout=20_000)

            # If still on a login/checkpoint URL, login failed
            if "login" in page.url and "checkpoint" not in page.url:
                return False
            return True

        except Exception as exc:
            print(f"[Facebook] login error: {exc}")
            return False

    def _parse_card(self, card) -> Listing | None:
        try:
            href = card.get_attribute("href") or ""
            url  = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            # Price — usually in a span near the top of the card
            price_el = card.query_selector(
                'span[class*="x193iq5w"]:first-child, span[aria-label*="€"]'
            )
            if not price_el:
                # Try all spans and look for one that contains a price
                spans = card.query_selector_all("span")
                for s in spans:
                    txt = s.inner_text()
                    if "€" in txt or "EUR" in txt:
                        price_el = s
                        break

            price = self._parse_price(price_el.inner_text() if price_el else "0")

            # Title — look for the most descriptive span
            title_candidates = card.query_selector_all("span")
            title = "Unknown"
            for span in title_candidates:
                txt = span.inner_text().strip()
                # Likely title: non-empty, not just a price, reasonable length
                if txt and "€" not in txt and 5 < len(txt) < 120:
                    title = txt
                    break

            # Image
            img_el    = card.query_selector("img")
            image_url = img_el.get_attribute("src") if img_el else None

            # Location — FB Marketplace near Porto; fallback to "Porto"
            location = "Porto"
            for span in title_candidates:
                txt = span.inner_text().strip()
                if any(
                    city in txt.lower()
                    for city in ["porto", "aveiro", "gaia", "braga", "matosinhos"]
                ):
                    location = txt
                    break

            return Listing(
                title=title,
                price=price,
                condition=Condition.UNKNOWN,
                location=location,
                url=url,
                source=self.SOURCE_NAME,
                image_url=image_url,
            )
        except Exception as exc:
            print(f"[Facebook] card parse error: {exc}")
            return None
