from PyQt6.QtCore import QThread, pyqtSignal

from models import Listing, Condition
from scorer import score_listings, filter_listings
from scrapers import (
    OLXScraper, CustoJustoScraper, EbayScraper,
    BackMarketScraper, FacebookScraper,
)


class ScraperWorker(QThread):
    # Emitted for each site: (site_name, listings_found, progress_pct)
    site_done       = pyqtSignal(str, int, int)
    # Emitted with a status string (info / warning)
    status_msg      = pyqtSignal(str)
    # Final sorted list
    all_done        = pyqtSignal(list)

    def __init__(self, query: str, config: dict, filters: dict, parent=None):
        super().__init__(parent)
        self.query   = query
        self.config  = config
        self.filters = filters
        self._abort  = False

    def abort(self):
        self._abort = True

    # ------------------------------------------------------------------ #

    def run(self):
        enabled  = self.config.get("enabled_sites", {})
        max_r    = self.config.get("max_results_per_site", 30)
        headless = self.config.get("headless_browser", True)

        scrapers = []
        if enabled.get("olx",        True):
            scrapers.append(OLXScraper(max_results=max_r, headless=headless))
        if enabled.get("custojusto", True):
            scrapers.append(CustoJustoScraper(max_results=max_r, headless=headless))
        if enabled.get("ebay",       True):
            scrapers.append(EbayScraper(max_results=max_r))
        if enabled.get("backmarket", True):
            scrapers.append(BackMarketScraper(max_results=max_r, headless=headless))
        if enabled.get("facebook",   False):
            scrapers.append(FacebookScraper(
                email=self.config.get("fb_email",    ""),
                password=self.config.get("fb_password", ""),
                max_results=max_r,
                headless=headless,
            ))

        total        = len(scrapers)
        all_listings = []

        for idx, scraper in enumerate(scrapers):
            if self._abort:
                self.status_msg.emit("Scan aborted.")
                break

            name = scraper.SOURCE_NAME
            self.status_msg.emit(f"Scanning {name}…")

            try:
                results = scraper.scrape(self.query)
            except Exception as exc:
                self.status_msg.emit(f"⚠ {name}: {exc}")
                results = []

            all_listings.extend(results)
            pct = int(((idx + 1) / total) * 100)
            self.site_done.emit(name, len(results), pct)

        # Apply post-scan filters
        conditions = self.filters.get("conditions")
        filtered   = filter_listings(
            all_listings,
            max_price=self.filters.get("max_price"),
            min_price=self.filters.get("min_price"),
            conditions=conditions if conditions else None,
        )

        # Score and sort
        scored = score_listings(filtered, weights=self.config.get("weights"))
        self.all_done.emit(scored)
