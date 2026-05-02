from typing import List
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .base import BaseScraper
from models import Listing, Condition


_GRADE_MAP = {
    "pristine":  Condition.NEW,
    "excellent": Condition.LIKE_NEW,
    "excelente": Condition.LIKE_NEW,
    "good":      Condition.GOOD,
    "bom":       Condition.GOOD,
    "fair":      Condition.USED,
    "aceitável": Condition.USED,
    "premium":   Condition.LIKE_NEW,
}


class BackMarketScraper(BaseScraper):
    SOURCE_NAME = "BackMarket.pt"
    BASE_URL    = "https://www.backmarket.pt"

    def scrape(self, query: str) -> List[Listing]:
        q   = query.replace(" ", "+")
        url = f"{self.BASE_URL}/pt-pt/search?q={q}"
        listings: List[Listing] = []

        try:
            with sync_playwright() as p:
                browser = self._new_browser(p)
                ctx     = self._new_context(browser)
                page    = ctx.new_page()

                page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                self._dismiss_cookies(page, '[data-qa="cookie-accept"]')

                # BackMarket is heavily React — wait for products
                try:
                    page.wait_for_selector(
                        '[data-qa="product-card"], [class*="productCard"], [class*="product-card"]',
                        timeout=18_000,
                    )
                except PWTimeout:
                    pass

                cards = page.query_selector_all(
                    '[data-qa="product-card"], [class*="productCard"]'
                )

                for card in cards[: self.max_results]:
                    lst = self._parse_card(card)
                    if lst:
                        listings.append(lst)

                browser.close()

        except Exception as exc:
            print(f"[BackMarket] error: {exc}")

        return listings

    def _parse_card(self, card) -> Listing | None:
        try:
            title_el = card.query_selector(
                '[data-qa="product-title"], h2, h3, [class*="title"], [class*="Title"]'
            )
            title = title_el.inner_text().strip() if title_el else "Unknown"

            link_el = card.query_selector("a[href]")
            href    = (link_el.get_attribute("href") or "") if link_el else ""
            url     = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            price_el = card.query_selector(
                '[data-qa="price"], [class*="price"], [class*="Price"]'
            )
            price = self._parse_price(price_el.inner_text() if price_el else "0")

            grade_el      = card.query_selector(
                '[data-qa="grade"], [class*="grade"], [class*="Grade"], [class*="condition"]'
            )
            condition_str = grade_el.inner_text().strip().lower() if grade_el else ""
            condition     = _GRADE_MAP.get(condition_str, Condition.GOOD)

            img_el    = card.query_selector("img")
            image_url = img_el.get_attribute("src") if img_el else None

            return Listing(
                title=title,
                price=price,
                condition=condition,
                location="Portugal",     # BackMarket ships nationwide
                url=url,
                source=self.SOURCE_NAME,
                image_url=image_url,
                raw_condition=condition_str,
            )
        except Exception as exc:
            print(f"[BackMarket] card parse error: {exc}")
            return None
