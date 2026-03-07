# src/logical_view/user_goals.py
"""
User's daily nutrition goals data model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class UserGoals:
    """
    User's daily nutrition goals.
    All fields are optional - system only optimizes for provided goals.
    """
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        """Convert to dictionary."""
        return {
            "calories": self.calories,
            "protein": self.protein,
            "carbs": self.carbs,
            "fat": self.fat,
            "fiber": self.fiber,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Optional[float]]) -> UserGoals:
        """Create from dictionary."""
        return cls(
            calories=data.get("calories"),
            protein=data.get("protein"),
            carbs=data.get("carbs"),
            fat=data.get("fat"),
            fiber=data.get("fiber"),
        )
