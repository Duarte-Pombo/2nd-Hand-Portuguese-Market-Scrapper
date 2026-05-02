from typing import List
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .base import BaseScraper
from models import Listing, Condition


class CustoJustoScraper(BaseScraper):
    SOURCE_NAME = "CustoJusto.pt"
    BASE_URL    = "https://www.custojusto.pt"

    def scrape(self, query: str) -> List[Listing]:
        q   = query.replace(" ", "+")
        url = f"{self.BASE_URL}/todo-portugal?q={q}"
        listings: List[Listing] = []

        try:
            with sync_playwright() as p:
                browser = self._new_browser(p)
                ctx     = self._new_context(browser)
                page    = ctx.new_page()

                page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                self._dismiss_cookies(page)

                # CustoJusto lazy-loads — give it a moment
                page.wait_for_timeout(3_000)

                # Try multiple possible card selectors
                card_selectors = [
                    "article.item",
                    ".listing-card",
                    "ul.items li",
                    "[class*='item-']",
                ]
                cards = []
                for sel in card_selectors:
                    try:
                        page.wait_for_selector(sel, timeout=5_000)
                        cards = page.query_selector_all(sel)
                        if cards:
                            break
                    except PWTimeout:
                        continue

                for card in cards[: self.max_results]:
                    lst = self._parse_card(card)
                    if lst:
                        listings.append(lst)

                browser.close()

        except Exception as exc:
            print(f"[CustoJusto] error: {exc}")

        return listings

    def _parse_card(self, card) -> Listing | None:
        try:
            title_el = card.query_selector(
                "h2, h3, a[class*='title'], span[class*='title'], [class*='Title']"
            )
            title = title_el.inner_text().strip() if title_el else "Unknown"

            link_el = card.query_selector("a[href]")
            href    = (link_el.get_attribute("href") or "") if link_el else ""
            url     = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            price_el = card.query_selector(
                "[class*='price'], [class*='Price'], span[class*='amount']"
            )
            price = self._parse_price(price_el.inner_text() if price_el else "0")

            loc_el   = card.query_selector("[class*='location'], [class*='Location']")
            location = loc_el.inner_text().strip() if loc_el else ""

            cond_el       = card.query_selector("[class*='condition'], [class*='state']")
            condition_str = cond_el.inner_text().strip() if cond_el else ""
            condition     = self._parse_condition(condition_str)

            img_el    = card.query_selector("img")
            image_url = img_el.get_attribute("src") if img_el else None

            if not title or title == "Unknown":
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
            print(f"[CustoJusto] card parse error: {exc}")
            return None
