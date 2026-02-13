# src/db/postgres.py
"""
Postgres helpers for ingestion and upsert operations.
"""
from __future__ import annotations

import os
from typing import Iterable, List, Dict, Any, Tuple

import psycopg

from src.logical_view import Food
from src.config import DATABASE_URL_ENV


def _get_database_url() -> str:
    url = os.getenv(DATABASE_URL_ENV)
    if not url:
        raise RuntimeError(
            f"Missing {DATABASE_URL_ENV}. Set it to your Supabase Postgres URL."
        )
    return url


def _food_rows(foods: Iterable[Food]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for food in foods:
        rows.append({
            "source": food.source,
            "food_id": food.food_id,
            "name": food.name,
            "brand": food.brand,
            "meal_category": food.meal_category,
            "calories": food.calories,
            "protein": food.protein,
            "carbs": food.carbs,
            "fat": food.fat,
            "fiber": food.fiber,
        })
    return rows


def _tag_rows(foods: Iterable[Food]) -> List[Tuple[str, int, str]]:
    rows: List[Tuple[str, int, str]] = []
    for food in foods:
        for tag in food.tags:
            rows.append((food.source, food.food_id, tag))
    return rows


def upsert_foods(foods: List[Food]) -> int:
    """
    Upsert foods and tags into Postgres.

    Returns:
        Number of foods processed.
    """
    if not foods:
        return 0

    rows = _food_rows(foods)
    tag_rows = _tag_rows(foods)

    with psycopg.connect(_get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO foods (
                    source, food_id, name, brand, meal_category,
                    calories, protein, carbs, fat, fiber, updated_at
                )
                VALUES (
                    %(source)s, %(food_id)s, %(name)s, %(brand)s, %(meal_category)s,
                    %(calories)s, %(protein)s, %(carbs)s, %(fat)s, %(fiber)s, now()
                )
                ON CONFLICT (source, food_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    brand = EXCLUDED.brand,
                    meal_category = EXCLUDED.meal_category,
                    calories = EXCLUDED.calories,
                    protein = EXCLUDED.protein,
                    carbs = EXCLUDED.carbs,
                    fat = EXCLUDED.fat,
                    fiber = EXCLUDED.fiber,
                    updated_at = now()
                """,
                rows,
            )

            # Replace tags for updated foods.
            key_rows = [(food.source, food.food_id) for food in foods]
            cur.executemany(
                "DELETE FROM food_tags WHERE source = %s AND food_id = %s",
                key_rows,
            )
            if tag_rows:
                cur.executemany(
                    """
                    INSERT INTO food_tags (source, food_id, tag)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (source, food_id, tag) DO NOTHING
                    """,
                    tag_rows,
                )

    return len(foods)
