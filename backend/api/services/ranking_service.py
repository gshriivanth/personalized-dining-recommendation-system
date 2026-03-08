# api/services/ranking_service.py
"""
Adapter between Pydantic API models and the existing FoodRanker dataclasses.

The ranking layer uses Python dataclasses (Food, UserGoals, ConsumedToday).
The API layer uses Pydantic models validated from JSON.
This service handles the conversion so neither layer needs to change.
"""
from __future__ import annotations

import math
from typing import List, Optional, Set

from src.implicit_ranking.food_ranking import FoodRanker, RankingContext
from src.logical_view.food import Food
from src.logical_view.user_goals import UserGoals
from src.logical_view.consumed_today import ConsumedToday

from api.models.food import FoodResponse
from api.models.recommendations import (
    ConsumedTodayInput,
    GoalsRequest,
    NutrientHighlight,
    RecommendationItem,
)

_ranker = FoodRanker()


def _to_user_goals(goals: GoalsRequest) -> UserGoals:
    return UserGoals(
        calories=goals.calories,
        protein=goals.protein,
        carbs=goals.carbs,
        fat=goals.fat,
        fiber=goals.fiber,
    )


def _to_consumed_today(consumed: ConsumedTodayInput) -> ConsumedToday:
    ct = ConsumedToday()
    ct.calories = consumed.calories
    ct.protein = consumed.protein
    ct.carbs = consumed.carbs
    ct.fat = consumed.fat
    ct.fiber = consumed.fiber
    return ct


def _food_to_response(food: Food) -> FoodResponse:
    return FoodResponse(
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
    )


def _build_nutrient_highlights(
    rec: dict,
    goals: UserGoals,
    consumed: ConsumedToday,
    serving_size: float,
    meals_remaining: int,
) -> List[NutrientHighlight]:
    """Build structured nutrient highlight badges for mobile UI."""
    highlights: List[NutrientHighlight] = []
    meals = max(1, meals_remaining)

    nutrient_meta = [
        ("calories", "kcal"),
        ("protein", "g"),
        ("carbs", "g"),
        ("fat", "g"),
        ("fiber", "g"),
    ]

    for nutrient, unit in nutrient_meta:
        goal_val = getattr(goals, nutrient)
        consumed_val = getattr(consumed, nutrient)
        food_val = rec.get(nutrient, 0.0)

        if goal_val is None or food_val == 0.0:
            continue

        remaining = max(0.0, goal_val - consumed_val)
        per_meal_target = remaining / meals
        if per_meal_target <= 0:
            continue

        pct = int(round((food_val / per_meal_target) * 100))
        highlights.append(NutrientHighlight(
            nutrient=nutrient,
            value=round(food_val, 1),
            unit=unit,
            pct_of_meal_target=pct,
        ))

    # Sort: calories first, then by pct descending
    highlights.sort(key=lambda h: (h.nutrient != "calories", -(h.pct_of_meal_target or 0)))
    return highlights[:4]  # cap at 4 highlights for card UI


def rank_foods(
    candidate_foods: List[Food],
    goals_input: GoalsRequest,
    consumed_input: ConsumedTodayInput,
    meal_type: Optional[str],
    time_of_day: Optional[str],
    favorites: List[int],
    top_k: int,
    serving_size: float,
    source_prefixes: Optional[List[str]] = None,
) -> List[RecommendationItem]:
    goals = _to_user_goals(goals_input)
    consumed = _to_consumed_today(consumed_input)
    context = RankingContext(
        meal_type=meal_type,
        time_of_day=time_of_day,
        favorites=set(favorites),
    )

    from src.implicit_ranking.food_ranking import get_meals_remaining
    meals_remaining = get_meals_remaining(context)

    raw_recs = _ranker.recommend(
        candidate_foods=candidate_foods,
        goals=goals,
        consumed=consumed,
        context=context,
        top_k=top_k,
        serving_size=serving_size,
        source_prefixes=source_prefixes,
    )

    results: List[RecommendationItem] = []
    for rec in raw_recs:
        food: Food = rec["food"]
        highlights = _build_nutrient_highlights(rec, goals, consumed, serving_size, meals_remaining)
        food_resp = _food_to_response(food)

        results.append(RecommendationItem(
            food=food_resp,
            score=round(rec["score"], 3),
            explanation=rec["explanation"],
            nutrient_highlights=highlights,
            serving_size_g=serving_size,
        ))

    return results
