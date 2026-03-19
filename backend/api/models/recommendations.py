# api/models/recommendations.py
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from api.models.food import FoodResponse
from api.models.user import GoalsRequest


class ConsumedTodayInput(BaseModel):
    calories: float = 0.0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    fiber: float = 0.0


class NutrientHighlight(BaseModel):
    """Structured highlight for mobile UI — one badge per nutrient."""
    nutrient: str       # "protein", "calories", "carbs", "fat", "fiber"
    value: float
    unit: str           # "g" or "kcal"
    pct_of_meal_target: Optional[int] = None  # percentage, e.g. 91


class RecommendationItem(BaseModel):
    food: FoodResponse
    score: float
    explanation: str
    nutrient_highlights: List[NutrientHighlight] = []
    serving_size_g: float


class DiningRecommendRequest(BaseModel):
    user_id: Optional[str] = None
    hall: str = Field(..., description="brandywine or anteatery")
    meal_period: Optional[str] = None  # breakfast, lunch, dinner
    goals: GoalsRequest
    consumed_today: ConsumedTodayInput = ConsumedTodayInput()
    favorites: List[int] = []
    top_k: int = Field(default=8, ge=1, le=30)
    serving_size_g: float = Field(default=100.0, ge=10.0)


class DiningRecommendResponse(BaseModel):
    hall: str
    meal_period: Optional[str]
    recommendations: List[RecommendationItem]


class ExploreRecommendRequest(BaseModel):
    user_id: Optional[str] = None
    query: Optional[str] = None  # optional keyword filter
    meal_type: Optional[str] = None
    category: Optional[str] = None
    required_tags: List[str] = []
    goals: GoalsRequest
    consumed_today: ConsumedTodayInput = ConsumedTodayInput()
    favorites: List[int] = []
    top_k: int = Field(default=10, ge=1, le=30)
    serving_size_g: float = Field(default=100.0, ge=10.0)


class ExploreRecommendResponse(BaseModel):
    query: Optional[str]
    recommendations: List[RecommendationItem]
