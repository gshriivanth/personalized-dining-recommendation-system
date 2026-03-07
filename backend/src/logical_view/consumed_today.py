# src/logical_view/consumed_today.py
"""
Tracks nutrients consumed so far today.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.logical_view.food import Food


@dataclass
class ConsumedToday:
    """
    Nutrients consumed so far today.
    """
    calories: float = 0.0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    fiber: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "calories": self.calories,
            "protein": self.protein,
            "carbs": self.carbs,
            "fat": self.fat,
            "fiber": self.fiber,
        }

    def add_food(self, food: "Food", serving_size: float = 100.0) -> None:
        """
        Add a food's nutrients to consumed totals.

        Args:
            food: Food item to add
            serving_size: Serving size in grams (default 100g)
        """
        multiplier = serving_size / 100.0
        self.calories += food.calories * multiplier
        self.protein += food.protein * multiplier
        self.carbs += food.carbs * multiplier
        self.fat += food.fat * multiplier
        self.fiber += food.fiber * multiplier
