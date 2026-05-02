import re
import sys
import os
from abc import ABC, abstractmethod
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Listing, Condition, CONDITION_MAP


class BaseScraper(ABC):
    SOURCE_NAME = "unknown"

    def __init__(self, max_results: int = 30, headless: bool = True):
        self.max_results = max_results
        self.headless    = headless

    @abstractmethod
    def scrape(self, query: str) -> List[Listing]:
        pass

    # ------------------------------------------------------------------ #
    #  Shared helpers                                                       #
    # ------------------------------------------------------------------ #

    def _parse_price(self, raw: str) -> float:
        if not raw:
            return 0.0
            
        # Strip everything except digits, dot, comma
        cleaned = re.sub(r"[^\d.,]", "", raw.strip())
        if not cleaned:
            return 0.0
            
        # European format handling
        if "," in cleaned and "." in cleaned:
            # e.g. 1.200,50 -> 1200.50
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # e.g. 1200,50 -> 1200.50
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned:
            # Only dot exists. E.g. "1.000" or "1.50"
            # If there are exactly 3 digits after the dot, treat it as a thousands separator.
            if re.search(r"\.\d{3}$", cleaned) and cleaned.count(".") == 1:
                cleaned = cleaned.replace(".", "")
                
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _parse_condition(self, raw: str) -> Condition:
        if not raw:
            return Condition.UNKNOWN
        lower = raw.lower().strip()
        for key, cond in CONDITION_MAP.items():
            if key in lower:
                return cond
        return Condition.UNKNOWN

    def _browser_args(self) -> list:
        return ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]

    def _new_browser(self, playwright):
        return playwright.chromium.launch(
            headless=self.headless,
            args=self._browser_args(),
        )

    def _new_context(self, browser):
        return browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="pt-PT",
            viewport={"width": 1280, "height": 900},
        )

    def _dismiss_cookies(self, page, *selectors: str) -> None:
        """Try clicking any of the given consent selectors, silently."""
        defaults = [
            '[id*="onetrust-accept"]',
            '[class*="cookie-accept"]',
            'button[aria-label*="Accept"]',
            '#acceptAllBtn',
            '[data-qa="cookie-accept"]',
        ]
        for sel in list(selectors) + defaults:
            try:
                page.click(sel, timeout=2000)
                return
            except Exception:
                pass
