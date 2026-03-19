# api/routers/dining.py
"""
Dining hall endpoints:
  GET  /v1/dining/halls         — list halls with open/closed status
  GET  /v1/dining/menu          — current menu for a hall + meal period
  POST /v1/dining/recommend     — personalized dining recommendations
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException

from api.models.food import FoodResponse
from api.models.recommendations import (
    DiningRecommendRequest,
    DiningRecommendResponse,
)
from api.services import dining_service, ranking_service

router = APIRouter(prefix="/v1/dining", tags=["Dining Hall"])

VALID_HALLS = {"brandywine", "anteatery"}
VALID_PERIODS = {"breakfast", "lunch", "dinner"}


@router.get("/halls")
def list_halls() -> List[dict]:
    """Return all halls with current open/closed status and active meal period."""
    return dining_service.list_halls()


@router.get("/menu", response_model=List[FoodResponse])
def get_menu(
    hall: str = Query(..., description="brandywine or anteatery"),
    meal_period: Optional[str] = Query(None, description="breakfast, lunch, or dinner"),
) -> List[FoodResponse]:
    """Return the raw menu for a hall, optionally filtered by meal period."""
    hall = hall.lower()
    if hall not in VALID_HALLS:
        raise HTTPException(status_code=400, detail=f"Unknown hall: {hall}. Use: {VALID_HALLS}")
    if meal_period and meal_period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid meal_period. Use: {VALID_PERIODS}")

    foods = dining_service.fetch_dining_foods(hall, meal_period)
    return [FoodResponse.from_food(f) for f in foods]


@router.post("/recommend", response_model=DiningRecommendResponse)
def recommend_dining(body: DiningRecommendRequest) -> DiningRecommendResponse:
    """Return personalized ranked recommendations from a specific dining hall."""
    hall = body.hall.lower()
    if hall not in VALID_HALLS:
        raise HTTPException(status_code=400, detail=f"Unknown hall: {hall}")

    meal_period = body.meal_period or dining_service.get_current_meal_period()

    candidate_foods = dining_service.fetch_dining_foods(hall, meal_period)
    if not candidate_foods:
        return DiningRecommendResponse(
            hall=hall, meal_period=meal_period, recommendations=[]
        )

    # Determine time_of_day from meal_period for ranking context
    time_map = {"breakfast": "morning", "lunch": "afternoon", "dinner": "evening"}
    time_of_day = time_map.get(meal_period or "", "afternoon")

    recommendations = ranking_service.rank_foods(
        candidate_foods=candidate_foods,
        goals_input=body.goals,
        consumed_input=body.consumed_today,
        meal_type=meal_period,
        time_of_day=time_of_day,
        favorites=body.favorites,
        top_k=body.top_k,
        serving_size=body.serving_size_g,
        source_prefixes=[f"uci_dining_{hall}"],
    )

    return DiningRecommendResponse(
        hall=hall,
        meal_period=meal_period,
        recommendations=recommendations,
    )
