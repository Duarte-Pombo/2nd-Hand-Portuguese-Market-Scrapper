from typing import List, Optional
from models import Listing, Condition, CONDITION_SCORES


def score_listings(listings: List[Listing], weights: Optional[dict] = None) -> List[Listing]:
    """Score each listing and return sorted by deal_score descending."""
    if not listings:
        return listings

    w = weights or {"price": 0.50, "condition": 0.30, "location": 0.20}

    prices = [l.price for l in listings if l.price > 0]
    if not prices:
        return listings

    min_p = min(prices)
    max_p = max(prices)
    p_range = max_p - min_p if max_p != min_p else 1.0

    for lst in listings:
        # --- Price score: lower = better ---
        if lst.price > 0 and p_range > 0:
            price_score = 1.0 - ((lst.price - min_p) / p_range)
        elif lst.price > 0:
            price_score = 0.5
        else:
            price_score = 0.0

        # --- Condition score ---
        cond_score = CONDITION_SCORES.get(lst.condition, 0.40)

        # --- Location score: Porto/Aveiro preferred ---
        loc_score = 1.0 if lst.is_near_porto_aveiro else 0.35

        lst.deal_score = (
            price_score * w.get("price",     0.50) +
            cond_score  * w.get("condition", 0.30) +
            loc_score   * w.get("location",  0.20)
        )

    return sorted(listings, key=lambda x: x.deal_score, reverse=True)


def filter_listings(
    listings:   List[Listing],
    max_price:  Optional[float] = None,
    min_price:  Optional[float] = None,
    conditions: Optional[List[Condition]] = None,
    sources:    Optional[List[str]] = None,
    keyword:    Optional[str] = None,
) -> List[Listing]:
    result = listings

    if max_price and max_price > 0:
        result = [l for l in result if 0 < l.price <= max_price]
    if min_price and min_price > 0:
        result = [l for l in result if l.price >= min_price]
    if conditions:
        result = [l for l in result if l.condition in conditions]
    if sources:
        result = [l for l in result if l.source in sources]
    if keyword and keyword.strip():
        kw = keyword.lower()
        result = [l for l in result if kw in l.title.lower()]

    return result
