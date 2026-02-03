# src/ingest/dininghall_sources.py
"""
UCI Dining Hall Web Scraper

Scrapes menu data from UCI's dining halls (Brandywine and Anteatery)
from https://uci.mydininghub.com/en

Since there's no public API, we use web scraping with BeautifulSoup.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, cast
from dataclasses import dataclass, field
import requests
from bs4 import BeautifulSoup, Tag
import time

from src.logical_view import Food


# UCI Dining Hall URLs
UCI_DINING_BASE_URL = "https://uci.mydininghub.com/en"
DINING_HALLS = {
    "brandywine": "Brandywine",
    "anteatery": "Anteatery"
}


@dataclass
class DiningMenuItem:
    """
    Represents a single menu item from UCI dining halls.
    """
    name: str
    hall: str
    meal_period: str  # breakfast, lunch, dinner
    station: str  # serving station/category
    # Nutritional info (may be incomplete from web scraping)
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    # Additional metadata
    allergens: List[str] = field(default_factory=list)
    dietary_flags: List[str] = field(default_factory=list)  # vegetarian, vegan, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
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


class UCIDiningScraper:
    """
    Web scraper for UCI dining hall menus.
    """

    def __init__(self, timeout_s: int = 30):
        """
        Initialize scraper.

        Args:
            timeout_s: Request timeout in seconds
        """
        self.timeout_s = timeout_s
        self.session = requests.Session()
        # Set user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def fetch_page(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            requests.RequestException: If request fails
        """
        response = self.session.get(url, timeout=self.timeout_s)
        response.raise_for_status()
        return response.text

    def parse_menu_page(self, html: str, hall: str) -> List[DiningMenuItem]:
        """
        Parse dining hall menu page HTML.

        Args:
            html: HTML content
            hall: Dining hall name (Brandywine or Anteatery)

        Returns:
            List of DiningMenuItem objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        menu_items = []

        # Find all menu items
        meal_sections = soup.find_all(['div', 'section'],
                                     class_=lambda x: 'menu' in x.lower() if x else False)

        for section in meal_sections:
            # Cast to Tag for proper typing
            section_tag = cast(Tag, section)
            meal_period = self._extract_meal_period(section_tag)

            # Find individual menu items
            items = section_tag.find_all(['div', 'li', 'article'],
                                    class_=lambda x: ('item' in str(x).lower() or
                                                     'dish' in str(x).lower()) if x else False)

            for item in items:
                try:
                    menu_item = self._parse_menu_item(item, hall, meal_period)
                    if menu_item:
                        menu_items.append(menu_item)
                except Exception as e:
                    continue

        return menu_items

    def _extract_meal_period(self, section) -> str:
        """Extract meal period from section element."""
        text = section.get_text().lower()

        if 'breakfast' in text:
            return 'breakfast'
        elif 'lunch' in text:
            return 'lunch'
        elif 'dinner' in text:
            return 'dinner'
        else:
            return 'unknown'

    def _parse_menu_item(self, item_element, hall: str, meal_period: str) -> Optional[DiningMenuItem]:
        """Parse individual menu item element."""
        # Extract item name
        name_elem = item_element.find(['h3', 'h4', 'span', 'div'],
                                      class_=lambda x: 'name' in str(x).lower() if x else False)
        if not name_elem:
            name = item_element.get_text(strip=True)
        else:
            name = name_elem.get_text(strip=True)

        if not name:
            return None

        # Extract station/category
        station_elem = item_element.find(['span', 'div'],
                                        class_=lambda x: ('station' in str(x).lower() or
                                                         'category' in str(x).lower()) if x else False)
        station = station_elem.get_text(strip=True) if station_elem else "General"

        # Extract nutritional info
        nutrition = self._extract_nutrition_info(item_element)

        # Extract dietary flags and allergens
        dietary_flags = self._extract_dietary_flags(item_element)
        allergens = self._extract_allergens(item_element)

        return DiningMenuItem(
            name=name,
            hall=hall,
            meal_period=meal_period,
            station=station,
            calories=nutrition.get('calories'),
            protein=nutrition.get('protein'),
            carbs=nutrition.get('carbs'),
            fat=nutrition.get('fat'),
            fiber=nutrition.get('fiber'),
            allergens=allergens,
            dietary_flags=dietary_flags,
        )

    def _extract_nutrition_info(self, element) -> Dict[str, Optional[float]]:
        """Extract nutritional information from element."""
        nutrition: Dict[str, Optional[float]] = {
            'calories': None,
            'protein': None,
            'carbs': None,
            'fat': None,
            'fiber': None,
        }

        nutrition_elem = element.find(['div', 'section'],
                                     class_=lambda x: x and 'nutrition' in str(x).lower() if x else False)
        if not nutrition_elem:
            return nutrition

        text = nutrition_elem.get_text()
        import re

        # Extract nutrition values
        cal_match = re.search(r'(\d+)\s*cal', text, re.IGNORECASE)
        if cal_match:
            nutrition['calories'] = float(cal_match.group(1))

        pro_match = re.search(r'protein[:\s]*(\d+\.?\d*)\s*g', text, re.IGNORECASE)
        if pro_match:
            nutrition['protein'] = float(pro_match.group(1))

        carb_match = re.search(r'carb(?:ohydrate)?[:\s]*(\d+\.?\d*)\s*g', text, re.IGNORECASE)
        if carb_match:
            nutrition['carbs'] = float(carb_match.group(1))

        fat_match = re.search(r'fat[:\s]*(\d+\.?\d*)\s*g', text, re.IGNORECASE)
        if fat_match:
            nutrition['fat'] = float(fat_match.group(1))

        fiber_match = re.search(r'fiber[:\s]*(\d+\.?\d*)\s*g', text, re.IGNORECASE)
        if fiber_match:
            nutrition['fiber'] = float(fiber_match.group(1))

        return nutrition

    def _extract_dietary_flags(self, element) -> List[str]:
        """Extract dietary flags (vegetarian, vegan, etc.)."""
        flags = []
        text = element.get_text().lower()

        # Look for dietary indicators
        if 'vegan' in text:
            flags.append('vegan')
        if 'vegetarian' in text:
            flags.append('vegetarian')
        if 'gluten free' in text or 'gluten-free' in text:
            flags.append('gluten-free')
        if 'dairy free' in text or 'dairy-free' in text:
            flags.append('dairy-free')

        return flags

    def _extract_allergens(self, element) -> List[str]:
        """Extract allergen information."""
        allergens = []
        text = element.get_text().lower()

        common_allergens = [
            'milk', 'eggs', 'fish', 'shellfish', 'tree nuts',
            'peanuts', 'wheat', 'soybeans', 'soy'
        ]

        for allergen in common_allergens:
            if allergen in text:
                allergens.append(allergen)

        return allergens

    def scrape_dining_hall(self, hall: str, date: Optional[str] = None) -> List[DiningMenuItem]:
        """
        Scrape menu for a specific dining hall.

        Args:
            hall: Dining hall name ('brandywine' or 'anteatery')
            date: Optional date string (YYYY-MM-DD), defaults to today

        Returns:
            List of DiningMenuItem objects
        """
        if hall.lower() not in DINING_HALLS:
            raise ValueError(f"Invalid hall: {hall}. Must be one of {list(DINING_HALLS.keys())}")

        # Construct URL
        if date:
            url = f"{UCI_DINING_BASE_URL}/{hall.lower()}?date={date}"
        else:
            url = f"{UCI_DINING_BASE_URL}/{hall.lower()}"

        print(f"Scraping {DINING_HALLS[hall.lower()]} menu from {url}...")

        try:
            html = self.fetch_page(url)
            menu_items = self.parse_menu_page(html, DINING_HALLS[hall.lower()])
            print(f"  Found {len(menu_items)} menu items")
            return menu_items
        except Exception as e:
            print(f"  Error scraping {hall}: {e}")
            return []

    def scrape_all_halls(self, date: Optional[str] = None, delay_seconds: float = 1.0) -> Dict[str, List[DiningMenuItem]]:
        """
        Scrape menus from all dining halls.

        Args:
            date: Optional date string (YYYY-MM-DD)
            delay_seconds: Delay between requests

        Returns:
            Dictionary mapping hall names to lists of menu items
        """
        results = {}

        for hall_key in DINING_HALLS.keys():
            menu_items = self.scrape_dining_hall(hall_key, date)
            results[DINING_HALLS[hall_key]] = menu_items
            time.sleep(delay_seconds)

        return results

    def convert_to_foods(self, menu_items: List[DiningMenuItem], default_calories: float = 200.0) -> List[Food]:
        """
        Convert DiningMenuItem objects to Food objects.

        Args:
            menu_items: List of DiningMenuItem objects
            default_calories: Default calorie value if not available

        Returns:
            List of Food objects
        """
        foods = []

        for idx, item in enumerate(menu_items):
            # Generate unique food_id for UCI dining items (use negative IDs)
            food_id = -(idx + 1)

            # Use available nutrition data or defaults
            calories = item.calories if item.calories is not None else default_calories
            protein = item.protein if item.protein is not None else 0.0
            carbs = item.carbs if item.carbs is not None else 0.0
            fat = item.fat if item.fat is not None else 0.0
            fiber = item.fiber if item.fiber is not None else 0.0

            # Map meal period to meal category
            meal_category = item.meal_period if item.meal_period != 'unknown' else 'any'

            food = Food(
                food_id=food_id,
                name=item.name,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                fiber=fiber,
                meal_category=meal_category,
                tags=item.dietary_flags.copy(),
                brand=item.hall,
                source=f"uci_dining_{item.hall.lower()}",
            )

            foods.append(food)

        return foods
