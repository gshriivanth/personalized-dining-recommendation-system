# api/routers/explore.py
"""
Explore (non-dining hall) endpoints:
  GET  /v1/explore/search       — keyword search across USDA/non-dining foods
  POST /v1/explore/recommend    — personalized recommendations from indexed foods
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from api.dependencies import index_manager_dep
from api.models.food import FoodResponse
from api.models.recommendations import (
    ExploreRecommendRequest,
    ExploreRecommendResponse,
)
from api.services import ranking_service
from src.index.build_index import FoodIndexManager

router = APIRouter(prefix="/v1/explore", tags=["Explore"])

UCI_DINING_PREFIX = "uci_dining_"


def _is_non_dining(food) -> bool:
    return not food.source.startswith(UCI_DINING_PREFIX)


@router.get("/search", response_model=List[FoodResponse])
def search_foods(
    q: str = Query(..., min_length=1, description="Search query"),
    meal_type: Optional[str] = Query(None),
    max_calories: Optional[float] = Query(None, ge=0),
    top_k: int = Query(default=20, ge=1, le=100),
    index: FoodIndexManager = Depends(index_manager_dep),
) -> List[FoodResponse]:
    """Keyword search returning non-dining foods."""
    results = index.search(query=q, meal_type=meal_type, max_calories=max_calories)
    non_dining = [f for f in results if _is_non_dining(f)][:top_k]
    return [
        FoodResponse(
            food_id=f.food_id,
            name=f.name,
            source=f.source,
            brand=f.brand,
            meal_category=f.meal_category,
            calories=f.calories,
            protein=f.protein,
            carbs=f.carbs,
            fat=f.fat,
            fiber=f.fiber,
            tags=f.tags,
        )
        for f in non_dining
    ]


@router.post("/recommend", response_model=ExploreRecommendResponse)
def recommend_explore(
    body: ExploreRecommendRequest,
    index: FoodIndexManager = Depends(index_manager_dep),
) -> ExploreRecommendResponse:
    """Return personalized ranked recommendations from USDA/non-dining foods."""
    if body.query:
        candidates = index.search(query=body.query, meal_type=body.meal_type)
    else:
        # No query: use all indexed non-dining foods as candidates
        candidates = list(index.nutrient_index.foods.values())

    candidates = [f for f in candidates if _is_non_dining(f)]

    time_map = {"breakfast": "morning", "lunch": "afternoon", "dinner": "evening", "snack": "afternoon"}
    time_of_day = time_map.get(body.meal_type or "", "afternoon")

    recommendations = ranking_service.rank_foods(
        candidate_foods=candidates,
        goals_input=body.goals,
        consumed_input=body.consumed_today,
        meal_type=body.meal_type,
        time_of_day=time_of_day,
        favorites=body.favorites,
        top_k=body.top_k,
        serving_size=body.serving_size_g,
    )

    return ExploreRecommendResponse(
        query=body.query,
        recommendations=recommendations,
    )
