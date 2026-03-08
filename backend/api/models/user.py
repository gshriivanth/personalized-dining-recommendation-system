# api/models/user.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GoalsRequest(BaseModel):
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None


class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    goals: Optional[GoalsRequest] = None


class ProfileResponse(BaseModel):
    user_id: str
    name: str
    goals: GoalsRequest
    favorites: List[str] = []  # compound IDs: "source:food_id"
    created_at: datetime


class FavoriteCreate(BaseModel):
    source: str
    food_id: int
    food_name: str = ""  # snapshot stored so favorites display even when item is not cached


class FavoriteResponse(BaseModel):
    compound_id: str  # "source:food_id"
    source: str
    food_id: int
    name: str
