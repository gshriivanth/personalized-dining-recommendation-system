# api/services/dining_service.py
"""
Dining hall service.

Scraping policy
---------------
UCI dining menus are scraped **once per meal period per hall**.  The first
request that arrives during a new meal period triggers a live scrape; all
subsequent requests within that period are served from the in-memory cache
(src/cache/dining_cache).  The cache entry expires automatically at the end
of the meal period, so the next period's first request always fetches fresh
data.

Hall status (open/closed) is derived from meal_periods.get_current_period(),
not from the scraper, so it works even when the hall is between meal periods.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from src.cache import dining_cache
from src.cache.meal_periods import (
    get_current_period,
    MAIN_MEAL_PERIODS,
)
from src.ingest.dininghall_sources import UCIDiningScraper
from src.logical_view.food import Food

logger = logging.getLogger(__name__)

HALL_DISPLAY_NAMES = {
    "brandywine": "Brandywine",
    "anteatery": "Anteatery",
}

VALID_HALLS = set(HALL_DISPLAY_NAMES.keys())


# ---------------------------------------------------------------------------
# Hall status
# ---------------------------------------------------------------------------

def get_current_meal_period() -> Optional[str]:
    period = get_current_period()
    return period.name if period else None


def is_hall_open() -> bool:
    return get_current_period() is not None


def list_halls() -> List[dict]:
    period = get_current_period()
    return [
        {
            "id": hall_id,
            "name": display,
            "is_open": period is not None,
            "current_meal_period": period.name if period else None,
            "is_main_meal": (period.name in MAIN_MEAL_PERIODS) if period else False,
        }
        for hall_id, display in HALL_DISPLAY_NAMES.items()
    ]


# ---------------------------------------------------------------------------
# Menu fetching — cache-aside pattern
# ---------------------------------------------------------------------------

def fetch_dining_foods(
    hall: str,
    meal_period: Optional[str] = None,
) -> List[Food]:
    """
    Return Food objects for *hall* during the requested (or current) meal period.

    Cache behaviour:
    - If called during an active meal period AND the cache for that period is
      warm, return the cached menu without scraping.
    - If the cache is cold (first request of the period), scrape the dining
      hub, populate the cache, then return the fresh data.
    - If the hall is between meal periods and no explicit meal_period was
      requested, return an empty list.

    Filtering:
    - If *meal_period* is provided, only foods matching that meal_category (or
      'any') are returned.  This allows clients to request a specific period
      even while a different one is active.
    """
    current_period = get_current_period()

    # Try cache first (keyed on current meal period, regardless of filter)
    cached = dining_cache.get_cached_menu(hall)
    if cached is not None:
        return _filter_by_period(cached, meal_period)

    # Cache miss — scrape fresh data
    logger.info("Dining cache MISS for hall=%s — scraping live menu...", hall)
    try:
        scraper = UCIDiningScraper()
        all_items: List[Food] = scraper.scrape_all()
    except Exception as exc:
        logger.error("Scrape failed for hall=%s: %s", hall, exc)
        return []

    source_key = f"uci_dining_{hall}"
    hall_foods = [f for f in all_items if f.source == source_key]

    # Only cache when inside an active meal period so the TTL is meaningful
    if current_period is not None:
        dining_cache.set_cached_menu(hall, hall_foods)
    else:
        logger.debug(
            "Not in a meal period — scraped %d items but skipping cache", len(hall_foods)
        )

    return _filter_by_period(hall_foods, meal_period)


def _filter_by_period(foods: List[Food], meal_period: Optional[str]) -> List[Food]:
    if not meal_period:
        return foods
    return [f for f in foods if f.meal_category in (meal_period, "any")]
