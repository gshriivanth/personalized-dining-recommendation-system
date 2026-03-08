# src/db/user_db.py
"""
Database operations for user-facing data: profiles, goals, favorites, meal logs.

All operations require a `user_id` (UUID string) that matches the Supabase
auth.users id delivered in the JWT `sub` claim.  A trigger in the database
automatically creates a row in `profiles` when a new auth user is created,
so this module never needs to create profiles manually.

Table ownership:
  profiles              — one row per auth user (created by DB trigger)
  user_goals            — one row per user, upserted here
  user_favorites        — many rows per user; no FK to foods (dining items
                          are cached, not stored in DB)
  user_consumption_log  — append-only meal log
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID

import psycopg
import psycopg.rows

from src.config import DATABASE_URL_ENV


def _conn() -> psycopg.Connection:
    url = os.getenv(DATABASE_URL_ENV)
    if not url:
        raise RuntimeError(f"Missing {DATABASE_URL_ENV}.")
    return psycopg.connect(url, row_factory=psycopg.rows.dict_row)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Return the profile row for *user_id*, or None if not found.
    The row is created automatically by a database trigger when the user
    signs up via Supabase Auth.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, name, created_at FROM profiles WHERE user_id = %s",
                (user_id,),
            )
            return cur.fetchone()


def update_profile_name(user_id: str, name: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE profiles SET name = %s WHERE user_id = %s
                """,
                (name, user_id),
            )


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

def get_goals(user_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT calories, protein, carbs, fat, fiber, updated_at
                FROM user_goals WHERE user_id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()


def upsert_goals(user_id: str, goals: Dict[str, Optional[float]]) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_goals (user_id, calories, protein, carbs, fat, fiber, updated_at)
                VALUES (%(user_id)s, %(calories)s, %(protein)s, %(carbs)s, %(fat)s, %(fiber)s, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    calories   = EXCLUDED.calories,
                    protein    = EXCLUDED.protein,
                    carbs      = EXCLUDED.carbs,
                    fat        = EXCLUDED.fat,
                    fiber      = EXCLUDED.fiber,
                    updated_at = now()
                """,
                {"user_id": user_id, **goals},
            )


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

def get_favorites(user_id: str) -> List[Dict[str, Any]]:
    """
    Return all favorites for *user_id*.
    The `food_name` column stores a snapshot of the name at the time of
    favoriting so we can display it even when the dining item is not cached.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, source, food_id, food_name, added_at
                FROM user_favorites
                WHERE user_id = %s
                ORDER BY added_at DESC
                """,
                (user_id,),
            )
            return cur.fetchall()


def get_favorite_food_ids(user_id: str) -> List[int]:
    """Return just the food_ids so the ranking layer can use them as a set."""
    rows = get_favorites(user_id)
    return [r["food_id"] for r in rows]


def add_favorite(user_id: str, source: str, food_id: int, food_name: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_favorites (user_id, source, food_id, food_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, source, food_id) DO NOTHING
                """,
                (user_id, source, food_id, food_name),
            )


def remove_favorite(user_id: str, source: str, food_id: int) -> bool:
    """Returns True if a row was deleted."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM user_favorites
                WHERE user_id = %s AND source = %s AND food_id = %s
                """,
                (user_id, source, food_id),
            )
            return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Meal log (user_consumption_log)
# ---------------------------------------------------------------------------

def log_meal(
    user_id: str,
    source: str,
    food_id: int,
    food_name: str,
    serving_size_g: float,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    fiber: float,
    meal_type: Optional[str],
    consumed_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    ts = consumed_at or datetime.now(timezone.utc)
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_consumption_log
                    (user_id, source, food_id, food_name,
                     serving_size_g, calories, protein, carbs, fat, fiber,
                     meal_type, consumed_at)
                VALUES
                    (%(user_id)s, %(source)s, %(food_id)s, %(food_name)s,
                     %(serving_size_g)s, %(calories)s, %(protein)s, %(carbs)s,
                     %(fat)s, %(fiber)s, %(meal_type)s, %(consumed_at)s)
                RETURNING log_id, consumed_at
                """,
                {
                    "user_id": user_id,
                    "source": source,
                    "food_id": food_id,
                    "food_name": food_name,
                    "serving_size_g": serving_size_g,
                    "calories": calories,
                    "protein": protein,
                    "carbs": carbs,
                    "fat": fat,
                    "fiber": fiber,
                    "meal_type": meal_type,
                    "consumed_at": ts,
                },
            )
            row = cur.fetchone()
            return {
                "log_id": str(row["log_id"]),
                "user_id": user_id,
                "source": source,
                "food_id": food_id,
                "food_name": food_name,
                "serving_size_g": serving_size_g,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "fiber": fiber,
                "meal_type": meal_type,
                "logged_at": row["consumed_at"],
            }


def get_meals_today(user_id: str) -> List[Dict[str, Any]]:
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT log_id, source, food_id, food_name,
                       serving_size_g, calories, protein, carbs, fat, fiber,
                       meal_type, consumed_at
                FROM user_consumption_log
                WHERE user_id = %s AND consumed_at >= %s
                ORDER BY consumed_at
                """,
                (user_id, today_start),
            )
            rows = cur.fetchall()
            return [
                {
                    "log_id": str(r["log_id"]),
                    "source": r["source"],
                    "food_id": r["food_id"],
                    "food_name": r["food_name"],
                    "serving_size_g": r["serving_size_g"],
                    "calories": r["calories"],
                    "protein": r["protein"],
                    "carbs": r["carbs"],
                    "fat": r["fat"],
                    "fiber": r["fiber"],
                    "meal_type": r["meal_type"],
                    "logged_at": r["consumed_at"],
                }
                for r in rows
            ]


def delete_meal_log(user_id: str, log_id: str) -> bool:
    """Returns True if a row was deleted."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_consumption_log WHERE log_id = %s AND user_id = %s",
                (log_id, user_id),
            )
            return cur.rowcount > 0


# ---------------------------------------------------------------------------
# USDA food TTL cleanup
# ---------------------------------------------------------------------------

def delete_stale_usda_foods(older_than_days: int = 30) -> int:
    """
    Delete non-dining USDA foods that haven't been refreshed in *older_than_days* days.
    This is called at API startup; it can also be wired to a Supabase pg_cron job.
    Returns number of rows deleted.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM foods
                WHERE source NOT LIKE 'uci_dining_%%'
                  AND updated_at < now() - (%s || ' days')::interval
                """,
                (str(older_than_days),),
            )
            return cur.rowcount
