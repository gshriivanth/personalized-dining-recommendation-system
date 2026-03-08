# api/routers/meals.py
"""
Meal logging endpoints — backed by user_consumption_log in Supabase.

All endpoints require a valid Supabase JWT via `require_auth`.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import require_auth
from api.models.meal_log import ConsumedTodaySummary, MealLogCreate, MealLogEntry
import src.db.user_db as user_db

router = APIRouter(prefix="/v1/meals", tags=["Meals"])


@router.get("/today", response_model=ConsumedTodaySummary)
def get_consumed_today(user_id: str = Depends(require_auth)) -> ConsumedTodaySummary:
    """Return all meals logged today and macro totals."""
    rows = user_db.get_meals_today(user_id)
    entries = [MealLogEntry(**r) for r in rows]

    total = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0}
    for e in entries:
        for nutrient in total:
            total[nutrient] += getattr(e, nutrient)

    return ConsumedTodaySummary(
        date=date.today().isoformat(),
        entries=entries,
        **{f"total_{k}": v for k, v in total.items()},
    )


@router.post("", response_model=MealLogEntry, status_code=201)
def log_meal(
    body: MealLogCreate, user_id: str = Depends(require_auth)
) -> MealLogEntry:
    """Log a food item to the user's consumption log."""
    row = user_db.log_meal(
        user_id=user_id,
        source=body.source,
        food_id=body.food_id,
        food_name=body.food_name,
        serving_size_g=body.serving_size_g,
        calories=body.calories,
        protein=body.protein,
        carbs=body.carbs,
        fat=body.fat,
        fiber=body.fiber,
        meal_type=body.meal_type,
        consumed_at=body.logged_at,
    )
    return MealLogEntry(**row)


@router.delete("/{log_id}", status_code=204, response_model=None)
def delete_meal_log(
    log_id: str, user_id: str = Depends(require_auth)
) -> None:
    deleted = user_db.delete_meal_log(user_id, log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log entry not found.")
