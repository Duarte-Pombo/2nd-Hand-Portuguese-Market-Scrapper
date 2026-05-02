# Tech Scrapper

A PyQt6 desktop app that scrapes used tech listings from **OLX.pt**, **CustoJusto.pt**, **eBay.pt**, **BackMarket.pt**, and **Facebook Marketplace**, scores them automatically, and surfaces the best deals near Porto / Aveiro.

---

## Quick Start

```bash
# Run the setup script  (installs deps + Playwright browser)
bash setup.sh

# Launch
python main.py
```

> **Requires Python 3.11+** and an internet connection.

---

## How Deal Scoring Works

Each listing is scored 0–100 using a weighted formula:

| Factor | Default Weight | Higher score when… |
|---|---|---|
| **Price** | 50 % | Price is lower relative to other results |
| **Condition** | 30 % | Item is Novo / Como Novo |
| **Location** | 20 % | Item is near Porto or Aveiro |

You can adjust weights in **Settings**.  Location weighting never hides results — it just pushes local deals up the list.

---

## Site Notes

| Site | Method | Notes |
|---|---|---|
| OLX.pt | Playwright | Main source for PT listings |
| CustoJusto.pt | Playwright | Good variety, slightly slower |
| eBay.pt | requests + BS4 | Fastest; international sellers included |
| BackMarket.pt | Playwright | Professionally refurbished; grades mapped to conditions |
| Facebook Marketplace | Playwright + login | Requires your FB credentials in Settings |

---

## Facebook Marketplace

1. Open **Settings** (sidebar bottom)
2. Enter your Facebook email and password
3. Enable the "Facebook Marketplace" checkbox in the sidebar
4. **Tip:** Use a secondary FB account to avoid triggering security checks

---

## Scraper Resilience

Website HTML structures change frequently. If a scraper stops returning results:

- Check the console output (run `python main.py` in a terminal) for error messages
- The selectors are in `scrapers/<site>.py` — each `_parse_card` method has comments
- Open an issue or edit the CSS selectors to match the current site HTML

---

## File Structure

```
tech_deal_finder/
├── main.py          ← PyQt6 UI + entry point
├── models.py        ← Listing dataclass, Condition enum
├── scorer.py        ← Deal scoring & filtering logic
├── config.py        ← Settings persistence (~/.tech_deal_finder/config.json)
├── workers.py       ← QThread worker that orchestrates scrapers
├── scrapers/
│   ├── base.py      ← Shared utilities (price parsing, Playwright helpers)
│   ├── olx.py
│   ├── custojusto.py
│   ├── ebay.py
│   ├── backmarket.py
│   └── facebook.py
├── requirements.txt
└── setup.sh
```
