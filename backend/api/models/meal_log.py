# api/models/meal_log.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MealLogCreate(BaseModel):
    source: str
    food_id: int
    food_name: str
    serving_size_g: float = Field(default=100.0, ge=1.0)
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    logged_at: Optional[datetime] = None


class MealLogEntry(BaseModel):
    log_id: str
    source: str
    food_id: int
    food_name: str
    serving_size_g: float
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    meal_type: Optional[str]
    logged_at: datetime


class ConsumedTodaySummary(BaseModel):
    date: str  # YYYY-MM-DD
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    entries: List[MealLogEntry]
