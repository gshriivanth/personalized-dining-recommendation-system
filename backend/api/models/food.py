# api/models/food.py
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.logical_view.food import Food


class FoodResponse(BaseModel):
    food_id: int
    name: str
    source: str
    brand: str = ""
    meal_category: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    tags: List[str] = []
    category: str = ""
    taxonomy_path: List[str] = []

    # Extended nutrition label fields (None if unavailable)
    saturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    cholesterol: Optional[float] = None
    sodium: Optional[float] = None
    sugars: Optional[float] = None
    added_sugars: Optional[float] = None
    vitamin_d: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None
    potassium: Optional[float] = None

    # Dining-hall-specific fields (null for USDA foods)
    hall: Optional[str] = None
    station: Optional[str] = None
    meal_period: Optional[str] = None

    @classmethod
    def from_food(cls, food: "Food") -> "FoodResponse":
        return cls(
            food_id=food.food_id,
            name=food.name,
            source=food.source,
            brand=food.brand,
            meal_category=food.meal_category,
            calories=food.calories,
            protein=food.protein,
            carbs=food.carbs,
            fat=food.fat,
            fiber=food.fiber,
            tags=food.tags,
            category=food.category,
            taxonomy_path=food.taxonomy_path,
            saturated_fat=food.saturated_fat,
            trans_fat=food.trans_fat,
            cholesterol=food.cholesterol,
            sodium=food.sodium,
            sugars=food.sugars,
            added_sugars=food.added_sugars,
            vitamin_d=food.vitamin_d,
            calcium=food.calcium,
            iron=food.iron,
            potassium=food.potassium,
            hall=food.hall,
            station=food.station,
            meal_period=food.meal_period,
        )


class FoodSearchParams(BaseModel):
    q: str = Field(..., min_length=1, description="Search query")
    meal_type: Optional[str] = None
    max_calories: Optional[float] = None
    top_k: int = Field(default=20, ge=1, le=100)
