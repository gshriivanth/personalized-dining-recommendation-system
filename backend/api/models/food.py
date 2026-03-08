# api/models/food.py
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


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

    # Dining-hall-specific fields (null for USDA foods)
    hall: Optional[str] = None
    station: Optional[str] = None
    meal_period: Optional[str] = None


class FoodSearchParams(BaseModel):
    q: str = Field(..., min_length=1, description="Search query")
    meal_type: Optional[str] = None
    max_calories: Optional[float] = None
    top_k: int = Field(default=20, ge=1, le=100)
