# api/routers/explore.py
"""
Explore (non-dining hall) endpoints:
  GET  /v1/explore/search       — keyword search; falls back to USDA FDC API if DB empty
  POST /v1/explore/recommend    — when no query: show only user's non-dining favorites;
                                  when query present: rank matching non-dining foods
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from api.dependencies import index_manager_dep
from api.models.food import FoodResponse
from api.models.recommendations import (
    ExploreRecommendRequest,
    ExploreRecommendResponse,
)
from api.services import ranking_service
from src.db import upsert_foods
import src.db.user_db as user_db
from src.index.build_index import FoodIndexManager
from src.ingest.ingest_pipeline import parse_usda_food
from src.ingest.usda_fdc_client import USDAFoodDataCentralClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/explore", tags=["Explore"])

UCI_DINING_PREFIX = "uci_dining_"


def _is_non_dining(food) -> bool:
    return not food.source.startswith(UCI_DINING_PREFIX)


def _food_to_response(f) -> FoodResponse:
    return FoodResponse(
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


@router.get("/search", response_model=List[FoodResponse])
def search_foods(
    q: str = Query(..., min_length=1, description="Search query"),
    meal_type: Optional[str] = Query(None),
    max_calories: Optional[float] = Query(None, ge=0),
    top_k: int = Query(default=20, ge=1, le=100),
    index: FoodIndexManager = Depends(index_manager_dep),
) -> List[FoodResponse]:
    """
    Keyword search returning non-dining foods.
    If the in-memory index returns no results, falls back to the USDA FDC API,
    persists the new foods to the DB, and adds them to the live index.
    """
    results = index.search(query=q, meal_type=meal_type, max_calories=max_calories)
    non_dining = [f for f in results if _is_non_dining(f)][:top_k]

    if not non_dining:
        # Fallback: query USDA FDC API directly
        try:
            client = USDAFoodDataCentralClient()
            raw = client.search_foods(q, page_size=min(top_k, 25))
            parsed = [parse_usda_food(item) for item in raw.get("foods", [])]
            new_foods = [f for f in parsed if f is not None and _is_non_dining(f)]

            if new_foods:
                non_dining = new_foods[:top_k]
                logger.info("USDA fallback: fetched %d foods for query %r", len(new_foods), q)
                try:
                    upsert_foods(new_foods)
                    for food in new_foods:
                        index.add_food(food)
                except Exception as db_exc:
                    logger.warning("USDA fallback: DB upsert failed for query %r (results still returned): %s", q, db_exc)
        except Exception as exc:
            logger.warning("USDA fallback failed for query %r: %s", q, exc)

    return [_food_to_response(f) for f in non_dining]


@router.post("/recommend", response_model=ExploreRecommendResponse)
def recommend_explore(
    body: ExploreRecommendRequest,
    index: FoodIndexManager = Depends(index_manager_dep),
) -> ExploreRecommendResponse:
    """
    Personalized ranked recommendations from non-dining foods.

    - With a query: rank foods matching the query.
    - Without a query: rank only the user's non-dining favorites.
      Returns an empty list if the user has no such favorites.
    """
    if body.query:
        candidates = index.search(query=body.query, meal_type=body.meal_type)
        candidates = [f for f in candidates if _is_non_dining(f)]

        if not candidates:
            # Fallback: query USDA FDC API directly
            try:
                client = USDAFoodDataCentralClient()
                raw = client.search_foods(body.query, page_size=min(body.top_k, 25))
                parsed = [parse_usda_food(item) for item in raw.get("foods", [])]
                new_foods = [f for f in parsed if f is not None and _is_non_dining(f)]
                if new_foods:
                    candidates = new_foods
                    logger.info("USDA fallback in recommend: fetched %d foods for query %r", len(new_foods), body.query)
                    try:
                        upsert_foods(new_foods)
                        for food in new_foods:
                            index.add_food(food)
                    except Exception as db_exc:
                        logger.warning("USDA fallback: DB upsert failed for query %r (results still returned): %s", body.query, db_exc)
            except Exception as exc:
                logger.warning("USDA fallback failed in recommend for query %r: %s", body.query, exc)

    elif body.user_id:
        # No query — only surface foods the user has explicitly favorited
        fav_rows = user_db.get_favorites(body.user_id)
        non_dining_favs = [r for r in fav_rows if not r["source"].startswith(UCI_DINING_PREFIX)]
        if not non_dining_favs:
            return ExploreRecommendResponse(query=None, recommendations=[])

        fav_ids = {r["food_id"] for r in non_dining_favs}
        candidates = [
            f for f in index.nutrient_index.foods.values()
            if f.food_id in fav_ids and _is_non_dining(f)
        ]
        if not candidates:
            return ExploreRecommendResponse(query=None, recommendations=[])
    else:
        # No query and no user_id — nothing to show
        return ExploreRecommendResponse(query=None, recommendations=[])

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
