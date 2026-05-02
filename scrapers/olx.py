from typing import List
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .base import BaseScraper
from models import Listing, Condition


class OLXScraper(BaseScraper):
    SOURCE_NAME = "OLX.pt"
    BASE_URL    = "https://www.olx.pt"

    def scrape(self, query: str) -> List[Listing]:
        slug = query.replace(" ", "-")
        url  = f"{self.BASE_URL}/ads/q-{slug}/"
        listings: List[Listing] = []

        try:
            with sync_playwright() as p:
                browser = self._new_browser(p)
                ctx     = self._new_context(browser)
                page    = ctx.new_page()

                page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                self._dismiss_cookies(page)

                try:
                    page.wait_for_selector('[data-cy="l-card"]', timeout=15_000)
                except PWTimeout:
                    pass

                cards = page.query_selector_all('[data-cy="l-card"]')
                for card in cards[: self.max_results]:
                    lst = self._parse_card(card)
                    if lst:
                        listings.append(lst)

                browser.close()

        except Exception as exc:
            print(f"[OLX] error: {exc}")

        return listings

    def _parse_card(self, card) -> Listing | None:
        try:
            # Title
            title_el = card.query_selector(
                'h6, h4, [data-cy="ad-card-title"] h6, [data-cy="ad-card-title"] h4'
            )
            title = title_el.inner_text().strip() if title_el else "Unknown"

            # URL
            link_el = card.query_selector("a[href]")
            href    = (link_el.get_attribute("href") or "") if link_el else ""
            url     = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            # Price
            price_el = card.query_selector('[data-testid="ad-price"]')
            price    = self._parse_price(price_el.inner_text() if price_el else "0")

            # Location (first segment before "·" or "-")
            loc_el = card.query_selector('[data-testid="location-date"]')
            raw_loc = loc_el.inner_text().strip() if loc_el else ""
            location = raw_loc.split("·")[0].split(" - ")[0].strip()

            # Condition badge (not always present on card)
            badge_el      = card.query_selector('[data-testid="ad-condition"]')
            condition_str = badge_el.inner_text().strip() if badge_el else ""
            condition     = self._parse_condition(condition_str)

            # Image
            img_el    = card.query_selector("img")
            image_url = img_el.get_attribute("src") if img_el else None

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
            print(f"[OLX] card parse error: {exc}")
            return None
