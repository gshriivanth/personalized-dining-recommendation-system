# src/ingest/ingest_pipeline.py
"""
Unified data ingestion pipeline for the nutrition recommendation system.

Combines data from:
1. USDA FoodData Central API (structured nutrition data)
2. UCI Dining Halls (web scraping)

Outputs a unified dataset of Food objects.
"""
from __future__ import annotations

from typing import Dict, List, Any, Optional, Set
import time
from pathlib import Path
import json
import csv

from src.ingest.usda_fdc_client import USDAFoodDataCentralClient
from src.ingest.dininghall_sources import UCIDiningScraper
from src.logical_view import Food
from src.config import DATA_DIR
from src.db import upsert_foods


# USDA Nutrient IDs
NUTRIENT_IDS = {
    "energy": 1008,  # Energy (kcal)
    "protein": 1003,  # Protein (g)
    "carbs": 1005,  # Carbohydrate, by difference (g)
    "fat": 1004,  # Total lipid (fat) (g)
    "fiber": 1079,  # Fiber, total dietary (g)
}


# Common food queries organized by meal type
FOOD_QUERIES = {
    "breakfast": [
        "eggs", "oatmeal", "yogurt", "milk", "cereal", "pancakes",
        "bacon", "sausage", "toast", "bagel", "muffin", "granola"
    ],
    "lunch_dinner": [
        "chicken breast", "salmon", "beef", "pork", "tofu", "beans",
        "rice", "pasta", "quinoa", "bread", "potato", "sweet potato"
    ],
    "vegetables": [
        "broccoli", "spinach", "carrot", "tomato", "lettuce", "cucumber",
        "bell pepper", "onion", "mushroom", "zucchini"
    ],
    "fruits": [
        "apple", "banana", "orange", "strawberry", "blueberry", "grapes",
        "watermelon", "mango", "pineapple", "avocado"
    ],
    "snacks": [
        "almonds", "peanut butter", "cheese", "crackers", "chips",
        "protein bar", "trail mix", "popcorn"
    ],
}


def get_nutrient_value(food_data: Dict[str, Any], nutrient_id: int) -> float:
    """
    Extract nutrient value from USDA food data.

    Args:
        food_data: Raw USDA FDC API response for a single food
        nutrient_id: USDA nutrient number

    Returns:
        Nutrient value or 0.0 if not found
    """
    nutrients = food_data.get("foodNutrients", [])
    for nutrient in nutrients:
        if (nutrient.get("nutrientId") == nutrient_id or
            nutrient.get("nutrient", {}).get("id") == nutrient_id):
            return float(nutrient.get("amount", 0.0))
    return 0.0


def parse_usda_food(food_data: Dict[str, Any]) -> Optional[Food]:
    """
    Parse raw USDA FDC API food data into a Food object.

    Args:
        food_data: Raw USDA FDC API response for a single food

    Returns:
        Food object or None if required data is missing
    """
    try:
        fdc_id = food_data.get("fdcId")
        if not fdc_id:
            return None

        description = food_data.get("description", "Unknown Food")
        brand = food_data.get("brandOwner", "")

        # Extract nutrients
        calories = get_nutrient_value(food_data, NUTRIENT_IDS["energy"])
        protein = get_nutrient_value(food_data, NUTRIENT_IDS["protein"])
        carbs = get_nutrient_value(food_data, NUTRIENT_IDS["carbs"])
        fat = get_nutrient_value(food_data, NUTRIENT_IDS["fat"])
        fiber = get_nutrient_value(food_data, NUTRIENT_IDS["fiber"])

        # Skip foods with no nutritional data
        if calories == 0 and protein == 0 and carbs == 0 and fat == 0:
            return None

        # Infer meal category and tags
        meal_category = infer_meal_category(description)
        tags = infer_dietary_tags(description)

        return Food(
            food_id=int(fdc_id),
            name=description,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber,
            meal_category=meal_category,
            tags=tags,
            brand=brand,
            source="usda_fdc",
        )
    except Exception as e:
        print(f"Error parsing USDA food: {e}")
        return None


def infer_meal_category(description: str) -> str:
    """
    Infer meal category from food description.

    Args:
        description: Food description/name

    Returns:
        One of: breakfast, lunch, dinner, snack, any
    """
    desc_lower = description.lower()

    # Breakfast keywords
    breakfast_keywords = ["egg", "oatmeal", "yogurt", "cereal", "pancake",
                         "waffle", "bacon", "sausage", "bagel", "muffin", "granola"]
    if any(kw in desc_lower for kw in breakfast_keywords):
        return "breakfast"

    # Snack keywords
    snack_keywords = ["chip", "cracker", "cookie", "candy", "bar", "nut",
                     "trail mix", "popcorn", "snack"]
    if any(kw in desc_lower for kw in snack_keywords):
        return "snack"

    # Lunch/dinner proteins
    protein_keywords = ["chicken", "beef", "pork", "fish", "salmon", "tuna",
                       "turkey", "tofu", "steak"]
    if any(kw in desc_lower for kw in protein_keywords):
        return "lunch"

    return "any"


def infer_dietary_tags(description: str) -> List[str]:
    """
    Infer dietary tags from food description.

    Args:
        description: Food description/name

    Returns:
        List of dietary tags
    """
    tags = []
    desc_lower = description.lower()

    if "vegan" in desc_lower:
        tags.append("vegan")
    if "vegetarian" in desc_lower or "vegan" in desc_lower:
        tags.append("vegetarian")
    if "gluten free" in desc_lower or "gluten-free" in desc_lower:
        tags.append("gluten-free")
    if "organic" in desc_lower:
        tags.append("organic")

    return tags


class DataIngestionPipeline:
    """
    Main data ingestion pipeline that combines USDA and UCI dining data.
    """

    def __init__(
        self,
        usda_api_key: Optional[str] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            usda_api_key: USDA FDC API key (optional, uses env variable if not provided)
        """
        self.usda_client = USDAFoodDataCentralClient(
            api_key=usda_api_key,
        )
        self.uci_scraper = UCIDiningScraper()
        self.foods: List[Food] = []

    def fetch_usda_foods(
        self,
        max_foods: int = 1000,
        foods_per_query: int = 50,
        delay_seconds: float = 0.5,
        max_queries: Optional[int] = None,
    ) -> List[Food]:
        """
        Fetch diverse food dataset from USDA FDC API.

        Args:
            max_foods: Maximum total foods to fetch
            foods_per_query: Maximum foods per search query
            delay_seconds: Delay between API calls

        Returns:
            List of Food objects
        """
        foods: List[Food] = []
        seen_ids: Set[int] = set()

        # Flatten all queries
        all_queries = []
        for category_queries in FOOD_QUERIES.values():
            all_queries.extend(category_queries)
        if max_queries is not None:
            all_queries = all_queries[:max_queries]

        print(f"Fetching up to {max_foods} USDA foods using {len(all_queries)} queries...")

        for query in all_queries:
            if len(foods) >= max_foods:
                break

            try:
                print(f"  Searching for: {query}...")
                response = self.usda_client.search_foods(
                    query=query,
                    page_size=foods_per_query,
                    data_type=["Survey (FNDDS)", "Foundation", "Branded"]
                )

                foods_data = response.get("foods", [])
                parsed_count = 0

                for food_data in foods_data:
                    fdc_id = food_data.get("fdcId")

                    # Skip duplicates
                    if fdc_id in seen_ids:
                        continue

                    food = parse_usda_food(food_data)
                    if food:
                        foods.append(food)
                        seen_ids.add(fdc_id)
                        parsed_count += 1

                print(f"    Found {parsed_count} new foods (total: {len(foods)})")

                # Respect rate limits
                time.sleep(delay_seconds)

            except Exception as e:
                print(f"    Error searching for '{query}': {e}")
                continue

        print(f"\nTotal USDA foods fetched: {len(foods)}")
        return foods[:max_foods]

    def fetch_uci_dining_foods(
        self,
        date: Optional[str] = None,
        delay_seconds: float = 1.0
    ) -> List[Food]:
        """
        Scrape UCI dining hall menus and convert to Food objects.

        Args:
            date: Optional date string (YYYY-MM-DD)
            delay_seconds: Delay between requests

        Returns:
            List of Food objects
        """
        print("\nScraping UCI dining halls...")

        menu_items_by_hall = self.uci_scraper.scrape_all_halls(
            date=date,
            delay_seconds=delay_seconds
        )

        # Convert all menu items to foods
        all_menu_items = []
        for items in menu_items_by_hall.values():
            all_menu_items.extend(items)

        foods = self.uci_scraper.convert_to_foods(all_menu_items)

        print(f"Total UCI dining foods: {len(foods)}")
        return foods

    def run_full_pipeline(
        self,
        max_usda_foods: int = 1000,
        foods_per_query: int = 50,
        max_queries: Optional[int] = None,
        include_usda: bool = True,
        include_uci: bool = True,
        delay_seconds: float = 0.5,
    ) -> List[Food]:
        """
        Run the complete ingestion pipeline.

        Args:
            max_usda_foods: Maximum USDA foods to fetch
            foods_per_query: Maximum foods per USDA search query
            max_queries: Optional cap on number of USDA queries
            include_usda: Whether to include USDA FDC data
            include_uci: Whether to include UCI dining hall data
            delay_seconds: Delay between USDA API calls

        Returns:
            Combined list of all Food objects
        """
        print("=== Running Full Data Ingestion Pipeline ===\n")

        # Fetch USDA foods
        usda_foods: List[Food] = []
        if include_usda:
            usda_foods = self.fetch_usda_foods(
                max_foods=max_usda_foods,
                foods_per_query=foods_per_query,
                delay_seconds=delay_seconds,
                max_queries=max_queries,
            )

        # Fetch UCI dining foods
        uci_foods = []
        if include_uci:
            try:
                uci_foods = self.fetch_uci_dining_foods()
            except Exception as e:
                print(f"Warning: Failed to fetch UCI dining data: {e}")
                print("Continuing with USDA data only...")

        # Combine all foods
        self.foods = usda_foods + uci_foods

        print(f"\n=== Pipeline Complete ===")
        print(f"Total foods ingested: {len(self.foods)}")
        print(f"  - USDA FDC: {len(usda_foods)}")
        print(f"  - UCI Dining: {len(uci_foods)}")

        return self.foods

    def save_to_json(self, output_path: Path) -> None:
        """Save foods to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = [food.to_dict() for food in self.foods]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.foods)} foods to {output_path}")

    def save_to_csv(self, output_path: Path) -> None:
        """Save foods to CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.foods:
            print("No foods to save")
            return

        fieldnames = [
            "food_id", "name", "calories", "protein", "carbs", "fat", "fiber",
            "meal_category", "tags", "brand", "source"
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for food in self.foods:
                row = food.to_dict()
                # Convert list to string for CSV
                row["tags"] = ",".join(row["tags"])
                writer.writerow(row)

        print(f"Saved {len(self.foods)} foods to {output_path}")

    def save_to_db(self) -> None:
        """Upsert foods into Postgres."""
        if not self.foods:
            print("No foods to save")
            return
        count = upsert_foods(self.foods)
        print(f"Upserted {count} foods to Postgres")

    @classmethod
    def load_from_json(cls, input_path: Path) -> List[Food]:
        """Load foods from JSON file."""
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        foods = [Food.from_dict(item) for item in data]
        print(f"Loaded {len(foods)} foods from {input_path}")
        return foods

    def print_summary(self) -> None:
        """Print summary statistics about ingested data."""
        if not self.foods:
            print("No foods to summarize")
            return

        print("\n=== Summary Statistics ===")
        print(f"Total foods: {len(self.foods)}")

        # Count by source
        from collections import Counter
        sources = Counter(food.source for food in self.foods)
        print("\nFoods by source:")
        for source, count in sources.most_common():
            print(f"  {source}: {count}")

        # Count by meal category
        categories = Counter(food.meal_category for food in self.foods)
        print("\nFoods by meal category:")
        for category, count in categories.most_common():
            print(f"  {category}: {count}")

        # Average nutrients
        avg_calories = sum(f.calories for f in self.foods) / len(self.foods)
        avg_protein = sum(f.protein for f in self.foods) / len(self.foods)
        avg_carbs = sum(f.carbs for f in self.foods) / len(self.foods)
        avg_fat = sum(f.fat for f in self.foods) / len(self.foods)

        print("\nAverage nutrients (per 100g):")
        print(f"  Calories: {avg_calories:.1f} kcal")
        print(f"  Protein: {avg_protein:.1f}g")
        print(f"  Carbs: {avg_carbs:.1f}g")
        print(f"  Fat: {avg_fat:.1f}g")


def main():
    """
    Main entry point for data ingestion.
    """
    # Create pipeline
    pipeline = DataIngestionPipeline()

    # Run full pipeline
    pipeline.run_full_pipeline(max_usda_foods=1000, include_uci=True)

    # Save outputs to Postgres
    pipeline.save_to_db()

    # Print summary
    pipeline.print_summary()


if __name__ == "__main__":
    main()
