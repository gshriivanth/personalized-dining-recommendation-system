# src/ingest/dininghall_sources.py
"""
UCI Dining Hall Scraper

Fetches menu data from UCI's dining halls (Brandywine and Anteatery) via
the Elevate DXP GraphQL API used by uci.mydininghub.com.

The API requires a GET request (not POST) with query and variables as URL
parameters, plus specific Magento store headers.  The response encodes all
nutrition data inside a flat ``attributes`` list of ``{name, value}`` pairs.

Two-step fetch:
  1. ``getLocation`` — fetches station IDs/names and allergen/preference code
     mappings.  Cached per session so we only call it once per hall.
  2. ``getLocationRecipes`` (DAILY) — fetches the menu for a given date and
     meal period, then joins items via stationSkuMap → SKU → product.

No Playwright fallback is needed once the correct headers/method are used.
"""
from __future__ import annotations

import json
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import date as date_type
from typing import Any, Dict, List, Optional, Set

import requests

from src.logical_view import Food

logger = logging.getLogger(__name__)


def _stable_dining_food_id(hall: str, name: str) -> int:
    """
    Generate a deterministic negative ID so favorites/logs survive menu refreshes.
    """
    normalized = f"{hall.lower()}|{' '.join(name.lower().split())}"
    digest = hashlib.blake2b(normalized.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big") & 0x7FFF_FFFF_FFFF_FFFF
    return -max(1, value)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ELEVATE_GRAPHQL_URL = (
    "https://api.elevate-dxp.com/api/mesh/"
    "c087f756-cc72-4649-a36f-3a41b700c519/graphql"
)

# Display name → API locationUrlKey
DINING_HALLS: Dict[str, str] = {
    "brandywine": "Brandywine",
    "anteatery": "Anteatery",
}

# hall_key → Elevate DXP locationUrlKey
_LOCATION_URL_KEYS: Dict[str, str] = {
    "brandywine": "brandywine",
    "anteatery": "the-anteatery",
}

# Elevate DXP integer IDs for each named meal period
MEAL_PERIOD_IDS: Dict[str, int] = {
    "breakfast": 10,
    "brunch": 13,
    "lunch": 25,
    "afternoon_snack": 25,
    "dinner": 16,
    "evening_snack": 16,
}

# ---------------------------------------------------------------------------
# GraphQL queries
# ---------------------------------------------------------------------------

_GET_LOCATION_QUERY = """
query getLocation(
  $locationUrlKey: String!
  $sortOrder: Commerce_SortOrderEnum
) {
  getLocation(campusUrlKey: "campus", locationUrlKey: $locationUrlKey) {
    commerceAttributes {
      maxMenusDate
      children {
        id
        uid
        name
        position
      }
    }
  }
  Commerce_mealPeriods(sort_order: $sortOrder) {
    name
    id
    position
  }
  Commerce_attributesList(entityType: CATALOG_PRODUCT) {
    items {
      code
      options {
        value
        label
      }
    }
  }
}
"""

_GET_LOCATION_RECIPES_QUERY = """
query getLocationRecipes(
  $locationUrlKey: String!
  $date: String!
  $mealPeriod: Int
  $viewType: Commerce_MenuViewType!
) {
  getLocationRecipes(
    campusUrlKey: "campus"
    locationUrlKey: $locationUrlKey
    date: $date
    mealPeriod: $mealPeriod
    viewType: $viewType
  ) {
    locationRecipesMap {
      stationSkuMap {
        id
        skus
      }
    }
    products {
      items {
        sku
        name
        images {
          url
        }
        attributes {
          name
          value
        }
      }
    }
  }
}
"""

_GRAPHQL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) "
        "Gecko/20100101 Firefox/141.0"
    ),
    "Referer": "https://uci.mydininghub.com/",
    "content-type": "application/json",
    "store": "ch_uci_en",
    "magento-store-code": "ch_uci",
    "magento-website-code": "ch_uci",
    "magento-store-view-code": "ch_uci_en",
    "x-api-key": "ElevateAPIProd",
    "Origin": "https://uci.mydininghub.com",
}

# Attribute name → nutrition field
_NUTRITION_ATTR_MAP: Dict[str, str] = {
    "calories": "calories",
    "protein": "protein",
    "total_carbohydrates": "carbs",
    "total_fat": "fat",
    "dietary_fiber": "fiber",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DiningMenuItem:
    """A single menu item from a UCI dining hall."""

    name: str
    hall: str
    meal_period: str
    station: str
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    allergens: List[str] = field(default_factory=list)
    dietary_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hall": self.hall,
            "meal_period": self.meal_period,
            "station": self.station,
            "calories": self.calories,
            "protein": self.protein,
            "carbs": self.carbs,
            "fat": self.fat,
            "fiber": self.fiber,
            "allergens": self.allergens,
            "dietary_flags": self.dietary_flags,
        }


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

class UCIDiningScraper:
    """
    Fetches UCI dining hall menus via Elevate DXP GraphQL (GET requests).

    Usage::

        scraper = UCIDiningScraper()
        items = scraper.scrape_dining_hall("brandywine")   # today
        foods = scraper.convert_to_foods(items)
    """

    def __init__(self, timeout_s: int = 30):
        self.timeout_s = timeout_s
        # Per-session cache: hall_key → {station_id: station_name}
        self._station_cache: Dict[str, Dict[int, str]] = {}
        # Per-session cache: {allergen_code: allergen_name}
        self._allergen_codes: Dict[int, str] = {}
        # Per-session cache: {preference_code: preference_name}
        self._preference_codes: Dict[int, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape_dining_hall(
        self, hall: str, date: Optional[str] = None
    ) -> List[DiningMenuItem]:
        """
        Scrape the current meal period for *hall*.

        Args:
            hall: ``"brandywine"`` or ``"anteatery"``
            date: ISO date string (YYYY-MM-DD); defaults to today.

        Returns:
            List of ``DiningMenuItem`` objects (may be empty on failure).
        """
        hall = hall.lower()
        if hall not in DINING_HALLS:
            raise ValueError(
                f"Invalid hall: {hall!r}. Must be one of {list(DINING_HALLS)}"
            )

        date_str = date or date_type.today().isoformat()
        hall_display = DINING_HALLS[hall]
        meal_period_name = self._current_meal_period_name()
        meal_period_id = MEAL_PERIOD_IDS.get(meal_period_name, 25)

        logger.info(
            "Scraping %s — period=%s (id=%d) date=%s",
            hall_display, meal_period_name, meal_period_id, date_str,
        )

        # Ensure station/allergen metadata is loaded
        self._ensure_location_info(hall)

        items = self._fetch_menu(
            hall, hall_display, meal_period_name, meal_period_id, date_str
        )
        logger.info("Fetched %d items for %s", len(items), hall_display)
        return items

    def scrape_all_halls(
        self,
        date: Optional[str] = None,
        delay_seconds: float = 1.0,
    ) -> Dict[str, List[DiningMenuItem]]:
        """Scrape all halls; returns ``{display_name: [items]}``."""
        results: Dict[str, List[DiningMenuItem]] = {}
        for hall_key, hall_display in DINING_HALLS.items():
            results[hall_display] = self.scrape_dining_hall(hall_key, date)
            time.sleep(delay_seconds)
        return results

    def scrape_all(self, date: Optional[str] = None) -> List[Food]:
        """
        Scrape all halls and return a flat list of ``Food`` objects.
        Used by ``dining_service.py`` to populate the in-memory cache.
        """
        all_items: List[DiningMenuItem] = []
        for hall_key in DINING_HALLS:
            all_items.extend(self.scrape_dining_hall(hall_key, date))
        return self.convert_to_foods(all_items)

    def convert_to_foods(
        self,
        menu_items: List[DiningMenuItem],
        default_calories: float = 200.0,
    ) -> List[Food]:
        """Convert ``DiningMenuItem`` list → ``Food`` list."""
        foods: List[Food] = []
        for item in menu_items:
            food_id = _stable_dining_food_id(item.hall, item.name)
            calories = item.calories if item.calories is not None else default_calories
            meal_category = (
                item.meal_period if item.meal_period != "unknown" else "any"
            )
            foods.append(
                Food(
                    food_id=food_id,
                    name=item.name,
                    calories=calories,
                    protein=item.protein or 0.0,
                    carbs=item.carbs or 0.0,
                    fat=item.fat or 0.0,
                    fiber=item.fiber or 0.0,
                    meal_category=meal_category,
                    tags=list(item.dietary_flags),
                    brand=item.hall,
                    source=f"uci_dining_{item.hall.lower()}",
                    hall=item.hall,
                    station=item.station,
                    meal_period=item.meal_period,
                )
            )
        return foods

    # ------------------------------------------------------------------
    # Internal — location metadata
    # ------------------------------------------------------------------

    def _ensure_location_info(self, hall_key: str) -> None:
        """Populate station/allergen/preference caches for *hall_key* if needed."""
        if hall_key in self._station_cache:
            return

        location_url_key = _LOCATION_URL_KEYS[hall_key]
        variables = {"locationUrlKey": location_url_key, "sortOrder": "ASC"}

        try:
            data = self._graphql_get(_GET_LOCATION_QUERY, variables)
        except Exception as exc:
            logger.warning("getLocation failed for %s: %s", hall_key, exc)
            self._station_cache[hall_key] = {}
            return

        # Station id → name
        stations: Dict[int, str] = {}
        children = (
            data.get("data", {})
                .get("getLocation", {})
                .get("commerceAttributes", {})
                .get("children", [])
        )
        for child in children:
            sid = child.get("id")
            sname = child.get("name", "")
            if sid is not None:
                stations[int(sid)] = sname
        self._station_cache[hall_key] = stations

        # Allergen and preference code tables (same for all halls)
        if not self._allergen_codes:
            attr_items = (
                data.get("data", {})
                    .get("Commerce_attributesList", {})
                    .get("items", [])
            )
            for attr in attr_items:
                code = attr.get("code", "")
                if code == "allergens_intolerances":
                    for opt in attr.get("options", []):
                        try:
                            self._allergen_codes[int(opt["value"])] = opt["label"]
                        except (KeyError, ValueError):
                            pass
                elif code == "menu_preferences":
                    for opt in attr.get("options", []):
                        try:
                            self._preference_codes[int(opt["value"])] = opt["label"]
                        except (KeyError, ValueError):
                            pass

    # ------------------------------------------------------------------
    # Internal — menu fetch
    # ------------------------------------------------------------------

    def _fetch_menu(
        self,
        hall_key: str,
        hall_display: str,
        meal_period_name: str,
        meal_period_id: int,
        date_str: str,
    ) -> List[DiningMenuItem]:
        """Fetch and parse today's menu via getLocationRecipes."""
        location_url_key = _LOCATION_URL_KEYS[hall_key]
        variables: Dict[str, Any] = {
            "locationUrlKey": location_url_key,
            "date": date_str,
            "mealPeriod": meal_period_id,
            "viewType": "DAILY",
        }

        try:
            data = self._graphql_get(_GET_LOCATION_RECIPES_QUERY, variables)
        except Exception as exc:
            logger.warning("getLocationRecipes failed for %s: %s", hall_display, exc)
            return []

        recipes = data.get("data", {}).get("getLocationRecipes") or {}
        products_wrapper = recipes.get("products")
        location_map = recipes.get("locationRecipesMap")

        if not products_wrapper or not location_map:
            logger.debug(
                "getLocationRecipes returned null products/map for %s", hall_display
            )
            return []

        # Build SKU → parsed product dict
        sku_map = self._parse_products(products_wrapper.get("items", []))

        # Station id → name lookup for this hall
        station_names = self._station_cache.get(hall_key, {})

        items: List[DiningMenuItem] = []
        seen: Set[str] = set()

        for station_entry in location_map.get("stationSkuMap", []):
            station_id = station_entry.get("id")
            station_name = station_names.get(station_id, f"Station {station_id}")

            for sku in station_entry.get("skus", []):
                product = sku_map.get(sku)
                if product is None:
                    continue
                name = product["name"].strip()
                if not name or name in seen:
                    continue
                seen.add(name)

                items.append(
                    DiningMenuItem(
                        name=name,
                        hall=hall_display,
                        meal_period=meal_period_name,
                        station=station_name,
                        calories=product.get("calories"),
                        protein=product.get("protein"),
                        carbs=product.get("carbs"),
                        fat=product.get("fat"),
                        fiber=product.get("fiber"),
                        allergens=product.get("allergens", []),
                        dietary_flags=product.get("dietary_flags", []),
                    )
                )

        return items

    # ------------------------------------------------------------------
    # Internal — product attribute parsing
    # ------------------------------------------------------------------

    def _parse_products(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Convert a ``products.items`` list into a ``{sku: parsed_product}`` dict.

        Nutrition values live in the ``attributes`` list as ``{name, value}``
        pairs; e.g. ``{"name": "calories", "value": "320"}``.

        Some halls (e.g. Brandywine) use configurable products where nutrition
        is nested inside ``configurable_option_attributes`` as a JSON string.
        We fall back to the first option in that JSON when direct attributes
        are absent.
        """
        result: Dict[str, Dict[str, Any]] = {}

        for product in items:
            sku = product.get("sku", "")
            name = product.get("name", "")

            # Build attribute lookup
            attr_map: Dict[str, Any] = {}
            for attr in product.get("attributes", []):
                attr_map[attr.get("name", "")] = attr.get("value")

            # Nutrition — direct attributes first
            parsed: Dict[str, Any] = {"name": name}
            for attr_name, field_name in _NUTRITION_ATTR_MAP.items():
                parsed[field_name] = _to_float(attr_map.get(attr_name))

            # Fallback: configurable products (e.g. Brandywine) embed nutrition
            # inside a JSON string keyed by ``configurable_option_attributes``.
            # Use the first option's values when no direct nutrition was found.
            if all(parsed.get(f) is None for f in _NUTRITION_ATTR_MAP.values()):
                raw_opts = attr_map.get("configurable_option_attributes")
                if isinstance(raw_opts, str):
                    try:
                        opts = json.loads(raw_opts)
                        first_opt = next(iter(opts.values())) if opts else {}
                        for attr_name, field_name in _NUTRITION_ATTR_MAP.items():
                            parsed[field_name] = _to_float(first_opt.get(attr_name))
                        # Also pick up dietary flags from configurable option
                        pref_raw_cfg = first_opt.get("recipe_attributes", [])
                        if pref_raw_cfg and not attr_map.get("recipe_attributes"):
                            attr_map.setdefault("recipe_attributes", pref_raw_cfg)
                    except (json.JSONDecodeError, StopIteration):
                        pass

            # Allergens
            allergen_raw = attr_map.get("allergens_intolerances")
            allergen_codes: List[int] = []
            if isinstance(allergen_raw, list):
                allergen_codes = [int(c) for c in allergen_raw if _is_int(c)]
            elif allergen_raw is not None:
                if _is_int(allergen_raw):
                    allergen_codes = [int(allergen_raw)]
            parsed["allergens"] = [
                self._allergen_codes.get(c, str(c)) for c in allergen_codes
            ]

            # Dietary preferences
            pref_raw = attr_map.get("recipe_attributes")
            pref_codes: List[int] = []
            if isinstance(pref_raw, list):
                pref_codes = [int(c) for c in pref_raw if _is_int(c)]
            elif pref_raw is not None:
                if _is_int(pref_raw):
                    pref_codes = [int(pref_raw)]
            parsed["dietary_flags"] = [
                self._preference_codes.get(c, str(c)) for c in pref_codes
            ]

            result[sku] = parsed

        return result

    # ------------------------------------------------------------------
    # Internal — HTTP
    # ------------------------------------------------------------------

    def _graphql_get(
        self, query: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a GET request to the Elevate DXP GraphQL endpoint with
        ``query`` and ``variables`` as URL parameters (not a POST body).
        Raises on non-2xx or JSON parse failure.
        """
        resp = requests.get(
            ELEVATE_GRAPHQL_URL,
            headers=_GRAPHQL_HEADERS,
            params={
                "query": query,
                "variables": json.dumps(variables),
            },
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _current_meal_period_name() -> str:
        """Return the name of the currently active UCI meal period."""
        try:
            from src.cache.meal_periods import get_current_period
            period = get_current_period()
            return period.name if period else "lunch"
        except Exception:
            return "lunch"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> Optional[float]:
    """Safely convert *value* to float; return None on failure."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        import re
        m = re.search(r"-?\d+(\.\d+)?", value)
        if m:
            return float(m.group(0))
    return None


def _is_int(value: Any) -> bool:
    """Return True if *value* can be safely converted to int."""
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False
