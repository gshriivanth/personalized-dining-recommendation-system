# src/logical_view/food.py
"""
Food data model representing a single food item with nutritional information.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class Food:
    """
    Represents a single food item with nutritional information.

    This is the core data model for the nutrition recommendation system.
    Each food can be searched, indexed, and ranked based on its nutritional profile.

    Fields map to the schema used in this project:
      - food_id: Unique identifier (from USDA FDC or generated)
      - name: Food name (primary text field)
      - calories: Energy in kcal per 100g
      - protein: Protein in grams per 100g
      - carbs: Carbohydrates in grams per 100g
      - fat: Total fat in grams per 100g
      - fiber: Fiber in grams per 100g
      - meal_category: breakfast, lunch, dinner, snack, or 'any'
      - tags: Dietary tags (vegetarian, vegan, gluten-free, etc.)
      - brand: Brand name for branded foods
      - source: Data source (usda_fdc, user_created, etc.)
    """
    food_id: int
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    meal_category: str = "any"
    tags: List[str] = field(default_factory=list)
    brand: str = ""
    source: str = "usda_fdc"
    # Extended nutrition label fields (all per 100g, None if unavailable)
    saturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    cholesterol: Optional[float] = None     # mg
    sodium: Optional[float] = None          # mg
    sugars: Optional[float] = None          # g
    added_sugars: Optional[float] = None    # g
    vitamin_d: Optional[float] = None       # mcg
    calcium: Optional[float] = None         # mg
    iron: Optional[float] = None            # mg
    potassium: Optional[float] = None       # mg

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "food_id": self.food_id,
            "name": self.name,
            "calories": self.calories,
            "protein": self.protein,
            "carbs": self.carbs,
            "fat": self.fat,
            "fiber": self.fiber,
            "meal_category": self.meal_category,
            "tags": self.tags,
            "brand": self.brand,
            "source": self.source,
            "saturated_fat": self.saturated_fat,
            "trans_fat": self.trans_fat,
            "cholesterol": self.cholesterol,
            "sodium": self.sodium,
            "sugars": self.sugars,
            "added_sugars": self.added_sugars,
            "vitamin_d": self.vitamin_d,
            "calcium": self.calcium,
            "iron": self.iron,
            "potassium": self.potassium,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Food:
        """Create Food instance from dictionary."""
        return cls(
            food_id=data["food_id"],
            name=data["name"],
            calories=data["calories"],
            protein=data["protein"],
            carbs=data["carbs"],
            fat=data["fat"],
            fiber=data["fiber"],
            meal_category=data.get("meal_category", "any"),
            tags=data.get("tags", []),
            brand=data.get("brand", ""),
            source=data.get("source", "usda_fdc"),
            saturated_fat=data.get("saturated_fat"),
            trans_fat=data.get("trans_fat"),
            cholesterol=data.get("cholesterol"),
            sodium=data.get("sodium"),
            sugars=data.get("sugars"),
            added_sugars=data.get("added_sugars"),
            vitamin_d=data.get("vitamin_d"),
            calcium=data.get("calcium"),
            iron=data.get("iron"),
            potassium=data.get("potassium"),
        )

    def get_nutrient_vector(self) -> List[float]:
        """
        Get normalized nutrient vector for similarity scoring.
        Returns [calories, protein, carbs, fat, fiber].
        """
        return [self.calories, self.protein, self.carbs, self.fat, self.fiber]

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"Food(id={self.food_id}, name='{self.name}', "
            f"cal={self.calories:.1f}, pro={self.protein:.1f}g, "
            f"carb={self.carbs:.1f}g, fat={self.fat:.1f}g, fiber={self.fiber:.1f}g)"
        )
