# src/db/postgres.py
"""
Postgres helpers for ingestion and upsert operations.
"""
from __future__ import annotations

import os
from typing import Iterable, List, Dict, Any, Tuple, Optional

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
            "saturated_fat": food.saturated_fat,
            "trans_fat": food.trans_fat,
            "cholesterol": food.cholesterol,
            "sodium": food.sodium,
            "sugars": food.sugars,
            "added_sugars": food.added_sugars,
            "vitamin_d": food.vitamin_d,
            "calcium": food.calcium,
            "iron": food.iron,
            "potassium": food.potassium,
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
                    calories, protein, carbs, fat, fiber,
                    saturated_fat, trans_fat, cholesterol, sodium, sugars,
                    added_sugars, vitamin_d, calcium, iron, potassium, updated_at
                )
                VALUES (
                    %(source)s, %(food_id)s, %(name)s, %(brand)s, %(meal_category)s,
                    %(calories)s, %(protein)s, %(carbs)s, %(fat)s, %(fiber)s,
                    %(saturated_fat)s, %(trans_fat)s, %(cholesterol)s, %(sodium)s, %(sugars)s,
                    %(added_sugars)s, %(vitamin_d)s, %(calcium)s, %(iron)s, %(potassium)s, now()
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
                    saturated_fat = EXCLUDED.saturated_fat,
                    trans_fat = EXCLUDED.trans_fat,
                    cholesterol = EXCLUDED.cholesterol,
                    sodium = EXCLUDED.sodium,
                    sugars = EXCLUDED.sugars,
                    added_sugars = EXCLUDED.added_sugars,
                    vitamin_d = EXCLUDED.vitamin_d,
                    calcium = EXCLUDED.calcium,
                    iron = EXCLUDED.iron,
                    potassium = EXCLUDED.potassium,
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


def fetch_foods(
    limit: Optional[int] = None,
    sources: Optional[Iterable[str]] = None,
    source_prefixes: Optional[Iterable[str]] = None,
) -> List[Food]:
    """
    Fetch foods with tags from Postgres.

    Args:
        limit: Optional row limit
        sources: Optional exact sources to include
        source_prefixes: Optional source prefixes to include (e.g., "uci_dining_")

    Returns:
        List of Food objects
    """
    limit_clause = "LIMIT %(limit)s" if limit is not None else ""

    where_clauses = []
    params: Dict[str, Any] = {"limit": limit} if limit is not None else {}

    if sources:
        where_clauses.append("f.source = ANY(%(sources)s)")
        params["sources"] = list(sources)

    if source_prefixes:
        prefixes = [f"{prefix}%" for prefix in source_prefixes]
        where_clauses.append("f.source LIKE ANY(%(prefixes)s)")
        params["prefixes"] = prefixes

    where_sql = f"WHERE {' OR '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT
            f.source,
            f.food_id,
            f.name,
            f.brand,
            f.meal_category,
            f.calories,
            f.protein,
            f.carbs,
            f.fat,
            f.fiber,
            f.saturated_fat,
            f.trans_fat,
            f.cholesterol,
            f.sodium,
            f.sugars,
            f.added_sugars,
            f.vitamin_d,
            f.calcium,
            f.iron,
            f.potassium,
            COALESCE(array_agg(t.tag) FILTER (WHERE t.tag IS NOT NULL), '{{}}') AS tags
        FROM foods f
        LEFT JOIN food_tags t
            ON f.source = t.source AND f.food_id = t.food_id
        {where_sql}
        GROUP BY
            f.source, f.food_id, f.name, f.brand, f.meal_category,
            f.calories, f.protein, f.carbs, f.fat, f.fiber,
            f.saturated_fat, f.trans_fat, f.cholesterol, f.sodium, f.sugars,
            f.added_sugars, f.vitamin_d, f.calcium, f.iron, f.potassium
        ORDER BY f.source, f.food_id
        {limit_clause}
    """

    foods: List[Food] = []
    with psycopg.connect(_get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            for row in rows:
                (
                    source,
                    food_id,
                    name,
                    brand,
                    meal_category,
                    calories,
                    protein,
                    carbs,
                    fat,
                    fiber,
                    saturated_fat,
                    trans_fat,
                    cholesterol,
                    sodium,
                    sugars,
                    added_sugars,
                    vitamin_d,
                    calcium,
                    iron,
                    potassium,
                    tags,
                ) = row
                foods.append(
                    Food(
                        food_id=food_id,
                        name=name,
                        calories=calories,
                        protein=protein,
                        carbs=carbs,
                        fat=fat,
                        fiber=fiber,
                        meal_category=meal_category,
                        tags=list(tags) if tags else [],
                        brand=brand or "",
                        source=source,
                        saturated_fat=saturated_fat,
                        trans_fat=trans_fat,
                        cholesterol=cholesterol,
                        sodium=sodium,
                        sugars=sugars,
                        added_sugars=added_sugars,
                        vitamin_d=vitamin_d,
                        calcium=calcium,
                        iron=iron,
                        potassium=potassium,
                    )
                )
    return foods
