# src/index/inverted_index.py
"""
Core inverted index data structures for food search.

Implements keyword inverted index and nutrient vector index.
"""
from __future__ import annotations

from typing import List, Dict, Set, Optional
from collections import defaultdict
from dataclasses import dataclass
import re

from src.logical_view import Food


DEFAULT_STOPWORDS: Set[str] = {
    "a", "an", "and", "the", "of", "to", "in", "on", "for", "with", "by", "or"
}


def tokenize(
    text: str,
    remove_stopwords: bool = False,
    stopwords: Optional[Set[str]] = None,
) -> List[str]:
    """
    Tokenize text into searchable terms.

    Args:
        text: Input text to tokenize

    Returns:
        List of lowercase tokens
    """
    # Simple tokenization: lowercase and split on whitespace and punctuation
    # Remove punctuation and convert to lowercase
    text = text.lower()
    # Split on non-alphanumeric characters
    tokens = re.split(r'[^a-z0-9]+', text)
    # Filter out empty strings
    tokens = [t for t in tokens if t]
    if remove_stopwords:
        active_stopwords = stopwords if stopwords is not None else DEFAULT_STOPWORDS
        tokens = [t for t in tokens if t not in active_stopwords]
    return tokens


@dataclass
class KeywordIndex:
    """
    Keyword inverted index mapping terms to food IDs.

    Similar to professor's inverted index but simplified for food search.
    Maps: term -> list of food_ids containing that term
    """
    # term -> set of food_ids
    index: Dict[str, Set[int]]

    def __init__(self):
        """Initialize empty index."""
        self.index = defaultdict(set)

    def add_food(self, food: Food) -> None:
        """
        Add a food to the keyword index.

        Args:
            food: Food object to index
        """
        # Tokenize food name
        tokens = tokenize(food.name)

        # Add food_id to each token's posting list
        for token in set(tokens):  # Use set to avoid duplicates
            self.index[token].add(food.food_id)

        # Also index brand if present
        if food.brand:
            brand_tokens = tokenize(food.brand)
            for token in set(brand_tokens):
                self.index[token].add(food.food_id)

    def search(self, query: str) -> Set[int]:
        """
        Search for foods matching query terms (OR search).

        Args:
            query: Search query string

        Returns:
            Set of food_ids matching any query term
        """
        tokens = tokenize(query)
        if not tokens:
            return set()

        # OR search: return foods matching any token
        result_ids = set()
        for token in tokens:
            result_ids.update(self.index.get(token, set()))

        return result_ids

    def search_all(self, query: str) -> Set[int]:
        """
        Search for foods matching ALL query terms (AND search).

        Args:
            query: Search query string

        Returns:
            Set of food_ids matching all query terms
        """
        tokens = tokenize(query)
        if not tokens:
            return set()

        # AND search: intersect posting lists
        result_ids = self.index.get(tokens[0], set()).copy()
        for token in tokens[1:]:
            result_ids &= self.index.get(token, set())

        return result_ids

    def to_dict(self) -> Dict[str, List[int]]:
        """
        Convert index to JSON-serializable format.

        Returns:
            Dictionary mapping terms to lists of food IDs
        """
        return {term: sorted(list(ids)) for term, ids in self.index.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, List[int]]) -> KeywordIndex:
        """
        Load index from dictionary.

        Args:
            data: Dictionary mapping terms to lists of food IDs

        Returns:
            KeywordIndex instance
        """
        index = cls()
        for term, ids in data.items():
            index.index[term] = set(ids)
        return index


@dataclass
class NutrientVectorIndex:
    """
    Nutrient vector index for recommendation ranking.

    Stores each food as a nutrient vector [calories, protein, carbs, fat, fiber]
    to enable efficient filtering and scoring against user's remaining targets.
    """
    # food_id -> Food object
    foods: Dict[int, Food]

    def __init__(self):
        """Initialize empty index."""
        self.foods = {}

    def add_food(self, food: Food) -> None:
        """
        Add a food to the nutrient index.

        Args:
            food: Food object to index
        """
        self.foods[food.food_id] = food

    def get_food(self, food_id: int) -> Optional[Food]:
        """
        Retrieve a food by ID.

        Args:
            food_id: Food ID to retrieve

        Returns:
            Food object or None if not found
        """
        return self.foods.get(food_id)

    def get_foods(self, food_ids: Set[int]) -> List[Food]:
        """
        Retrieve multiple foods by IDs.

        Args:
            food_ids: Set of food IDs to retrieve

        Returns:
            List of Food objects (excluding missing IDs)
        """
        foods = []
        for food_id in food_ids:
            food = self.get_food(food_id)
            if food:
                foods.append(food)
        return foods

    def filter_by_meal_category(
        self,
        meal_type: str,
        food_ids: Optional[Set[int]] = None
    ) -> List[Food]:
        """
        Filter foods by meal category.

        Args:
            meal_type: Meal category (breakfast, lunch, dinner, snack, any)
            food_ids: Optional set of food IDs to filter (if None, filters all foods)

        Returns:
            List of Food objects matching the meal category
        """
        if food_ids is None:
            food_ids = set(self.foods.keys())

        filtered = []
        for food_id in food_ids:
            food = self.get_food(food_id)
            if food and (food.meal_category == meal_type or food.meal_category == "any"):
                filtered.append(food)

        return filtered

    def filter_by_calorie_budget(
        self,
        max_calories: float,
        foods: Optional[List[Food]] = None
    ) -> List[Food]:
        """
        Filter foods that fit within calorie budget.

        Args:
            max_calories: Maximum calories allowed
            foods: Optional list of foods to filter (if None, filters all foods)

        Returns:
            List of Food objects within calorie budget
        """
        if foods is None:
            foods = list(self.foods.values())

        return [food for food in foods if food.calories <= max_calories]

    def to_dict(self) -> Dict[int, Dict]:
        """
        Convert index to JSON-serializable format.

        Returns:
            Dictionary mapping food IDs to food data
        """
        return {food_id: food.to_dict() for food_id, food in self.foods.items()}

    @classmethod
    def from_dict(cls, data: Dict[int, Dict]) -> NutrientVectorIndex:
        """
        Load index from dictionary.

        Args:
            data: Dictionary mapping food IDs to food data

        Returns:
            NutrientVectorIndex instance
        """
        index = cls()
        for food_id_str, food_data in data.items():
            food_id = int(food_id_str)
            food = Food.from_dict(food_data)
            index.foods[food_id] = food
        return index
