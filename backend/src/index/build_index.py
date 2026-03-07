# src/index/build_index.py
"""
Index building and management for food search system.

Provides high-level interface for building and using keyword + nutrient indexes.
"""
from __future__ import annotations

from typing import List, Optional
from pathlib import Path
import json

from src.logical_view import Food
from src.index.inverted_index import KeywordIndex, NutrientVectorIndex


class FoodIndexManager:
    """
    Manager class combining keyword and nutrient indexes.
    
    Provides unified interface for building, searching, and persisting indexes.
    """

    def __init__(self):
        """Initialize both indexes."""
        self.keyword_index = KeywordIndex()
        self.nutrient_index = NutrientVectorIndex()

    def build_index(self, foods: List[Food]) -> None:
        """
        Build both indexes from a list of foods.

        Args:
            foods: List of Food objects to index
        """
        print(f"Building indexes for {len(foods)} foods...")

        for food in foods:
            self.keyword_index.add_food(food)
            self.nutrient_index.add_food(food)

        print(f"Indexed {len(self.keyword_index.index)} unique terms")
        print(f"Indexed {len(self.nutrient_index.foods)} foods")

    def search(
        self,
        query: Optional[str] = None,
        meal_type: Optional[str] = None,
        max_calories: Optional[float] = None,
    ) -> List[Food]:
        """
        Search and filter foods.

        Args:
            query: Optional text search query
            meal_type: Optional meal category filter
            max_calories: Optional calorie budget filter

        Returns:
            List of Food objects matching all criteria
        """
        # Start with keyword search if query provided
        if query:
            food_ids = self.keyword_index.search(query)
            foods = self.nutrient_index.get_foods(food_ids)
        else:
            # No query, start with all foods
            foods = list(self.nutrient_index.foods.values())

        # Apply meal category filter
        if meal_type:
            food_ids = {f.food_id for f in foods}
            foods = self.nutrient_index.filter_by_meal_category(meal_type, food_ids)

        # Apply calorie budget filter
        if max_calories is not None:
            foods = self.nutrient_index.filter_by_calorie_budget(max_calories, foods)

        return foods

    def save_to_json(self, output_path: Path) -> None:
        """
        Save indexes to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "keyword_index": self.keyword_index.to_dict(),
            "nutrient_index": self.nutrient_index.to_dict(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved indexes to {output_path}")

    @classmethod
    def load_from_json(cls, input_path: Path) -> FoodIndexManager:
        """
        Load indexes from JSON file.

        Args:
            input_path: Path to input JSON file

        Returns:
            FoodIndexManager instance
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        manager = cls()
        manager.keyword_index = KeywordIndex.from_dict(data["keyword_index"])
        manager.nutrient_index = NutrientVectorIndex.from_dict(data["nutrient_index"])

        print(f"Loaded indexes from {input_path}")
        return manager
