# api/routers/profile.py
"""
User profile, goals, and favorites endpoints.

Authentication: every endpoint requires a valid Supabase JWT.
The authenticated user_id is extracted from the token by `require_auth`.
Clients pass: Authorization: Bearer <supabase_access_token>

Profile rows are created automatically by a Supabase database trigger when
the user signs up, so there is no POST /v1/profile endpoint — Supabase Auth
owns account creation.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import require_auth
from api.models.user import (
    FavoriteCreate,
    FavoriteResponse,
    GoalsRequest,
    ProfileResponse,
)
import src.db.user_db as user_db

router = APIRouter(prefix="/v1/profile", tags=["Profile"])


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(user_id: str = Depends(require_auth)) -> ProfileResponse:
    """Return the authenticated user's profile."""
    row = user_db.get_profile(user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found. Try signing in again.")
    goals_row = user_db.get_goals(user_id) or {}
    favorites = user_db.get_favorites(user_id)
    return ProfileResponse(
        user_id=str(row["user_id"]),
        name=row["name"] or "",
        goals=GoalsRequest(
            calories=goals_row.get("calories"),
            protein=goals_row.get("protein"),
            carbs=goals_row.get("carbs"),
            fat=goals_row.get("fat"),
            fiber=goals_row.get("fiber"),
        ),
        favorites=[f"{f['source']}:{f['food_id']}" for f in favorites],
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

@router.get("/me/goals", response_model=GoalsRequest)
def get_goals(user_id: str = Depends(require_auth)) -> GoalsRequest:
    row = user_db.get_goals(user_id)
    if not row:
        return GoalsRequest()
    return GoalsRequest(
        calories=row.get("calories"),
        protein=row.get("protein"),
        carbs=row.get("carbs"),
        fat=row.get("fat"),
        fiber=row.get("fiber"),
    )


@router.put("/me/goals", response_model=GoalsRequest)
def update_goals(body: GoalsRequest, user_id: str = Depends(require_auth)) -> GoalsRequest:
    user_db.upsert_goals(user_id, body.model_dump())
    return body


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

@router.get("/me/favorites", response_model=list[FavoriteResponse])
def get_favorites(user_id: str = Depends(require_auth)) -> list[FavoriteResponse]:
    rows = user_db.get_favorites(user_id)
    return [
        FavoriteResponse(
            compound_id=f"{r['source']}:{r['food_id']}",
            source=r["source"],
            food_id=r["food_id"],
            name=r.get("food_name", ""),
        )
        for r in rows
    ]


@router.post("/me/favorites", response_model=FavoriteResponse, status_code=201)
def add_favorite(
    body: FavoriteCreate, user_id: str = Depends(require_auth)
) -> FavoriteResponse:
    user_db.add_favorite(user_id, body.source, body.food_id, body.food_name)
    return FavoriteResponse(
        compound_id=f"{body.source}:{body.food_id}",
        source=body.source,
        food_id=body.food_id,
        name=body.food_name,
    )


@router.delete("/me/favorites/{source}/{food_id}", status_code=204, response_model=None)
def remove_favorite(
    source: str,
    food_id: int,
    user_id: str = Depends(require_auth),
) -> None:
    deleted = user_db.remove_favorite(user_id, source, food_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Favorite not found.")
