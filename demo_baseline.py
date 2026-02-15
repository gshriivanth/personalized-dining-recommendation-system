#!/usr/bin/env python3
"""
Implementation Demo

Demonstrates the end-to-end demo of the personalized nutrition
recommendation system.

This script shows:
1. Data ingestion from USDA FDC API and UCI dining halls
2. Indexing (keyword + nutrient vector)
3. Ranking algorithm with context-aware recommendations
"""
import os
from pathlib import Path

import psycopg

from src.logical_view import Food, UserGoals, ConsumedToday
from src.ingest.ingest_pipeline import DataIngestionPipeline
from src.config import USDA_FDC_API_KEY_ENV
from src.index import FoodIndexManager
from src.implicit_ranking.food_ranking import FoodRanker, RankingContext, calculate_remaining_targets, get_meals_remaining
from src.db import fetch_foods, upsert_foods


def create_sample_dataset() -> list[Food]:
    """
    Create a sample food dataset for demonstration.

    In production, this would come from the ingestion pipeline.
    """
    print("=== Creating Sample Food Dataset ===\n")

    foods = [
        # Breakfast items
        Food(1, "Scrambled Eggs", 155, 13.0, 1.1, 11.0, 0.0, "breakfast", ["high-protein"], "Generic", "usda_fdc"),
        Food(2, "Oatmeal with Berries", 71, 2.5, 12.0, 1.4, 1.7, "breakfast", ["vegetarian"], "Generic", "usda_fdc"),
        Food(3, "Greek Yogurt", 97, 10.0, 3.6, 5.0, 0.0, "breakfast", [], "Chobani", "usda_fdc"),
        Food(4, "Whole Wheat Toast", 247, 13.0, 41.0, 3.0, 6.0, "breakfast", [], "Generic", "usda_fdc"),

        # Lunch/Dinner items
        Food(5, "Grilled Chicken Breast", 165, 31.0, 0.0, 3.6, 0.0, "lunch", ["high-protein"], "Generic", "usda_fdc"),
        Food(6, "Salmon Fillet", 206, 22.0, 0.0, 13.0, 0.0, "lunch", ["high-protein"], "Generic", "usda_fdc"),
        Food(7, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5, "any", [], "Generic", "usda_fdc"),
        Food(8, "Quinoa", 368, 14.0, 64.0, 6.1, 7.0, "any", ["vegetarian"], "Generic", "usda_fdc"),
        Food(9, "Grilled Tofu", 76, 8.1, 1.9, 4.8, 0.3, "lunch", ["vegan", "vegetarian"], "Generic", "usda_fdc"),

        # Vegetables
        Food(10, "Broccoli", 34, 2.8, 7.0, 0.4, 2.6, "any", ["vegan", "vegetarian"], "Generic", "usda_fdc"),
        Food(11, "Spinach", 23, 2.9, 3.6, 0.4, 2.2, "any", ["vegan", "vegetarian"], "Generic", "usda_fdc"),
        Food(12, "Sweet Potato", 86, 1.6, 20.0, 0.1, 3.0, "any", ["vegan", "vegetarian"], "Generic", "usda_fdc"),
        Food(13, "Carrots", 41, 0.9, 10.0, 0.2, 2.8, "any", ["vegan", "vegetarian"], "Generic", "usda_fdc"),

        # Fruits
        Food(14, "Apple", 52, 0.3, 14.0, 0.2, 2.4, "snack", ["vegan", "vegetarian"], "Generic", "usda_fdc"),
        Food(15, "Banana", 89, 1.1, 23.0, 0.3, 2.6, "snack", ["vegan", "vegetarian"], "Generic", "usda_fdc"),
        Food(16, "Strawberries", 32, 0.7, 7.7, 0.3, 2.0, "snack", ["vegan", "vegetarian"], "Generic", "usda_fdc"),

        # Snacks
        Food(17, "Almonds", 579, 21.0, 22.0, 50.0, 12.5, "snack", ["vegan", "vegetarian"], "Generic", "usda_fdc"),
        Food(18, "Peanut Butter", 588, 25.0, 20.0, 50.0, 6.0, "snack", ["vegetarian"], "Jif", "usda_fdc"),
        Food(19, "Protein Bar", 200, 20.0, 22.0, 7.0, 3.0, "snack", [], "Quest", "usda_fdc"),

        # UCI Dining Hall items (simulated)
        Food(-1, "Brandywine Grilled Chicken", 170, 30.0, 2.0, 4.0, 0.0, "lunch", [], "Brandywine", "uci_dining"),
        Food(-2, "Anteatery Veggie Bowl", 250, 8.0, 45.0, 6.0, 8.0, "lunch", ["vegetarian"], "Anteatery", "uci_dining"),
    ]

    print(f"Created {len(foods)} sample foods")
    print(f"  - Breakfast items: {sum(1 for f in foods if f.meal_category == 'breakfast')}")
    print(f"  - Lunch/Dinner items: {sum(1 for f in foods if f.meal_category == 'lunch')}")
    print(f"  - Snacks: {sum(1 for f in foods if f.meal_category == 'snack')}")
    print(f"  - Any category: {sum(1 for f in foods if f.meal_category == 'any')}")
    print()

    return foods


def load_or_ingest_foods(
    max_usda_foods: int = 100,
    foods_per_query: int = 10,
    max_queries: int = 10,
    include_uci: bool = False,
) -> list[Food]:
    """
    Load cached foods if available, otherwise ingest a small real-data subset.

    The ingest path is rate-limited to respect USDA FDC API limits.
    """
    try:
        foods = fetch_foods(limit=None)
    except RuntimeError as exc:
        raise RuntimeError(
            "Missing DATABASE_URL. Set it to your Supabase Postgres URL to run the demo."
        ) from exc
    except psycopg.OperationalError as exc:
        print(f"Warning: Could not connect to Postgres ({exc}). Falling back to sample dataset.\n")
        return create_sample_dataset()
    if foods:
        print(f"Loaded {len(foods)} foods from Postgres.\n")
        return foods

    api_key = os.getenv(USDA_FDC_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"Missing {USDA_FDC_API_KEY_ENV}. Set the env var to run the real-data demo."
        )

    pipeline = DataIngestionPipeline(
        usda_api_key=api_key,
    )
    foods = pipeline.run_full_pipeline(
        max_usda_foods=max_usda_foods,
        foods_per_query=foods_per_query,
        max_queries=max_queries,
        include_uci=include_uci,
        delay_seconds=0.0,
    )
    pipeline.save_to_db()
    return fetch_foods(limit=None)


def create_uci_dining_sample() -> list[Food]:
    """
    Realistic UCI dining hall menu items used to demonstrate the ingestion pipeline.

    Covers both halls (Brandywine and Anteatery), multiple meal periods, and a
    variety of macronutrient profiles so that lunch/dinner recommendations look
    plausible.  Negative food_ids keep them distinct from USDA FDC records.
    """
    return [
        # ── Brandywine Hall — Lunch ──────────────────────────────────────
        Food(-101, "Brandywine Grilled Chicken Sandwich",
             450, 35.0, 40.0, 12.0, 2.0,
             "lunch", [], "Brandywine", "uci_dining_brandywine"),
        Food(-102, "Brandywine Caesar Salad with Chicken",
             320, 28.0, 15.0, 18.0, 4.0,
             "lunch", ["gluten-free"], "Brandywine", "uci_dining_brandywine"),
        Food(-103, "Brandywine Beef Burger",
             550, 32.0, 45.0, 25.0, 3.0,
             "lunch", [], "Brandywine", "uci_dining_brandywine"),
        Food(-104, "Brandywine Pasta Primavera",
             380, 12.0, 65.0, 8.0, 5.0,
             "lunch", ["vegetarian"], "Brandywine", "uci_dining_brandywine"),
        Food(-105, "Brandywine Tofu Rice Bowl",
             420, 18.0, 60.0, 12.0, 6.0,
             "lunch", ["vegan", "vegetarian"], "Brandywine", "uci_dining_brandywine"),
        # ── Brandywine Hall — Breakfast ──────────────────────────────────
        Food(-106, "Brandywine Scrambled Eggs",
             180, 14.0, 2.0, 13.0, 0.0,
             "breakfast", [], "Brandywine", "uci_dining_brandywine"),
        Food(-107, "Brandywine Oatmeal with Fresh Fruit",
             280, 8.0, 48.0, 5.0, 6.0,
             "breakfast", ["vegetarian"], "Brandywine", "uci_dining_brandywine"),
        # ── Anteatery Hall — Lunch ───────────────────────────────────────
        Food(-111, "Anteatery Teriyaki Salmon",
             380, 35.0, 20.0, 15.0, 1.0,
             "lunch", ["gluten-free"], "Anteatery", "uci_dining_anteatery"),
        Food(-112, "Anteatery Vegetable Stir-Fry with Tofu",
             280, 15.0, 35.0, 8.0, 4.0,
             "lunch", ["vegan", "vegetarian"], "Anteatery", "uci_dining_anteatery"),
        Food(-113, "Anteatery BBQ Pulled Pork Rice Bowl",
             480, 30.0, 55.0, 14.0, 3.0,
             "lunch", [], "Anteatery", "uci_dining_anteatery"),
        Food(-114, "Anteatery Black Bean Tacos",
             320, 14.0, 45.0, 10.0, 8.0,
             "lunch", ["vegetarian"], "Anteatery", "uci_dining_anteatery"),
        Food(-115, "Anteatery Greek Salad with Grilled Chicken",
             350, 26.0, 18.0, 18.0, 4.0,
             "lunch", ["gluten-free"], "Anteatery", "uci_dining_anteatery"),
        # ── Anteatery Hall — Breakfast ───────────────────────────────────
        Food(-116, "Anteatery Yogurt Parfait",
             250, 12.0, 38.0, 4.0, 2.0,
             "breakfast", ["vegetarian"], "Anteatery", "uci_dining_anteatery"),
        Food(-117, "Anteatery Avocado Toast with Egg",
             340, 16.0, 32.0, 16.0, 6.0,
             "breakfast", ["vegetarian"], "Anteatery", "uci_dining_anteatery"),
    ]


def demo_data_pipeline() -> list[Food]:
    """
    Demonstrate the full ingestion pipeline:
      A. Fetch UCI Dining Hall menu data
      B. Upsert to Postgres
      C. Retrieve the combined dataset from Postgres
    """
    print("=== A. Fetching UCI Dining Hall Menus ===\n")

    uci_foods = create_uci_dining_sample()

    brandywine = [f for f in uci_foods if f.source == "uci_dining_brandywine"]
    anteatery  = [f for f in uci_foods if f.source == "uci_dining_anteatery"]

    print(f"Retrieved {len(uci_foods)} items from UCI Dining Halls:")
    print(f"  Brandywine Hall: {len(brandywine)} items")
    for food in brandywine[:3]:
        print(f"    - {food.name}  ({food.calories:.0f} cal | "
              f"{food.protein:.0f}g protein | {food.meal_category})")
    print(f"  Anteatery Hall: {len(anteatery)} items")
    for food in anteatery[:3]:
        print(f"    - {food.name}  ({food.calories:.0f} cal | "
              f"{food.protein:.0f}g protein | {food.meal_category})")
    print()

    # ── B. Upsert ────────────────────────────────────────────────────────
    print("=== B. Upserting UCI Foods to Database ===\n")
    try:
        count = upsert_foods(uci_foods)
        print(f"Upserted {count} UCI dining items into Postgres.\n")
    except Exception as exc:
        print(f"  (DB upsert skipped — {exc})\n")

    # ── C. Retrieve ──────────────────────────────────────────────────────
    print("=== C. Retrieving All Foods from Database ===\n")
    try:
        all_foods = fetch_foods(limit=None)
        if all_foods:
            usda_n = sum(1 for f in all_foods if f.source == "usda_fdc")
            uci_n  = sum(1 for f in all_foods if f.source.startswith("uci_dining_"))
            other_n = len(all_foods) - usda_n - uci_n
            print(f"Retrieved {len(all_foods)} foods from Postgres:")
            print(f"  - USDA FDC:   {usda_n} foods")
            print(f"  - UCI Dining: {uci_n} foods")
            if other_n:
                print(f"  - Other:      {other_n} foods")
            print()
            return all_foods
    except Exception as exc:
        print(f"  (DB fetch failed — {exc})\n")

    # Fallback: in-memory dataset when DB is unavailable
    print("Using in-memory dataset (DB unavailable).\n")
    return uci_foods + create_sample_dataset()


def demo_indexing(foods: list[Food]):
    """Demonstrate indexing functionality."""
    print("=== Building Indexes ===\n")

    manager = FoodIndexManager()
    manager.build_index(foods)

    print("\n=== Testing Keyword Search ===\n")

    # Fixed queries that span breakfast, lunch, and plant-based options
    test_queries: list[str] = ["chicken", "salmon", "rice", "egg", "tofu"]

    for query in test_queries:
        results = manager.search(query=query)
        print(f"Query: '{query}' -> {len(results)} results")
        if results:
            for food in results[:3]:
                print(f"  - {food.name}")
        print()

    return manager


def demo_ranking(foods: list[Food]):
    """Demonstrate ranking algorithm."""
    print("=== Ranking Algorithm Demo ===\n")

    # Create user profile
    print("User Profile:")
    goals = UserGoals(
        calories=2000.0,
        protein=150.0,
        carbs=200.0,
        fat=65.0,
        fiber=30.0
    )
    print(f"  Daily Goals:")
    print(f"    - Calories: {goals.calories} kcal")
    print(f"    - Protein: {goals.protein}g")
    print(f"    - Carbs: {goals.carbs}g")
    print(f"    - Fat: {goals.fat}g")
    print(f"    - Fiber: {goals.fiber}g")

    # User has already eaten breakfast
    consumed = ConsumedToday()
    breakfast_food = Food(2, "Oatmeal with Berries", 71, 2.5, 12.0, 1.4, 1.7)
    consumed.add_food(breakfast_food, serving_size=200.0)  # 200g serving
    consumed.add_food(Food(3, "Greek Yogurt", 97, 10.0, 3.6, 5.0, 0.0), serving_size=150.0)

    print(f"\n  Already Consumed (Breakfast):")
    print(f"    - Calories: {consumed.calories:.0f} kcal")
    print(f"    - Protein: {consumed.protein:.1f}g")
    print(f"    - Carbs: {consumed.carbs:.1f}g")
    print(f"    - Fat: {consumed.fat:.1f}g")
    print(f"    - Fiber: {consumed.fiber:.1f}g")

    # Remaining targets
    remaining = calculate_remaining_targets(goals, consumed)

    def format_remaining(nutrient: str, unit: str, fmt: str) -> str:
        if nutrient not in remaining:
            return "N/A"
        return f"{remaining[nutrient]:{fmt}} {unit}"

    print(f"\n  Remaining Targets:")
    print(f"    - Calories: {format_remaining('calories', 'kcal', '.0f')}")
    print(f"    - Protein: {format_remaining('protein', 'g', '.1f')}")
    print(f"    - Carbs: {format_remaining('carbs', 'g', '.1f')}")
    print(f"    - Fat: {format_remaining('fat', 'g', '.1f')}")
    print(f"    - Fiber: {format_remaining('fiber', 'g', '.1f')}")

    # Use ingested foods as candidates
    candidate_foods = foods

    # Set up ranking context for lunch
    context = RankingContext(
        meal_type="lunch",
        time_of_day="afternoon",
        favorites={-101, -111}  # Brandywine Chicken Sandwich and Anteatery Salmon are favorites
    )

    meals_left = get_meals_remaining(context)
    print(f"\n  Context:")
    print(f"    - Meal Type: {context.meal_type}")
    print(f"    - Time of Day: {context.time_of_day}")
    print(f"    - Meals Remaining Today: {meals_left}")
    print(f"    - Favorite Foods: {len(context.favorites)}")

    print(f"\n  Per-Meal Targets ({meals_left} meal(s) left):")
    for nutrient, value in remaining.items():
        per_meal = value / meals_left
        unit = "kcal" if nutrient == "calories" else "g"
        fmt = ".0f" if nutrient == "calories" else ".1f"
        print(f"    - {nutrient.capitalize()}: {per_meal:{fmt}} {unit}")

    # Generate recommendations
    ranker = FoodRanker()
    recommendations = ranker.recommend(
        candidate_foods=candidate_foods,
        goals=goals,
        consumed=consumed,
        context=context,
        top_k=10,
        serving_size=100.0
    )

    print(f"\n=== Top {len(recommendations)} Recommendations for Lunch ===\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} (Score: {rec['score']:.2f})")
        print(f"   Nutrients: {rec['calories']:.0f} cal, {rec['protein']:.1f}g protein, "
              f"{rec['carbs']:.1f}g carbs, {rec['fat']:.1f}g fat")
        print(f"   {rec['explanation']}")
        print()


def demo_context_awareness(foods: list[Food]):
    """Demonstrate context-aware recommendations."""
    print("\n=== Context-Aware Recommendations Demo ===\n")

    goals = UserGoals(calories=2000.0, protein=150.0, carbs=200.0)
    consumed = ConsumedToday(calories=1200.0, protein=80.0, carbs=100.0)
    ranker = FoodRanker()

    # Scenario 1: Breakfast recommendations
    print("Scenario 1: Breakfast recommendations")
    context_breakfast = RankingContext(meal_type="breakfast")
    breakfast_recs = ranker.recommend(candidate_foods=foods, goals=goals,
                                       consumed=consumed, context=context_breakfast, top_k=3)

    for i, rec in enumerate(breakfast_recs, 1):
        print(f"  {i}. {rec['name']} - {rec['score']:.2f}")
    print()

    # Scenario 2: Lunch recommendations
    print("Scenario 2: Lunch recommendations")
    context_lunch = RankingContext(meal_type="lunch")
    lunch_recs = ranker.recommend(candidate_foods=foods, goals=goals,
                                   consumed=consumed, context=context_lunch, top_k=3)

    for i, rec in enumerate(lunch_recs, 1):
        print(f"  {i}. {rec['name']} - {rec['score']:.2f}")
    print()

    # Scenario 3: Low calorie budget
    print("Scenario 3: Almost reached calorie goal (only 300 cal remaining)")
    consumed_high_cal = ConsumedToday(calories=1700.0, protein=100.0, carbs=150.0)
    low_cal_recs = ranker.recommend(candidate_foods=foods, goals=goals,
                                     consumed=consumed_high_cal, context=RankingContext(), top_k=3)

    for i, rec in enumerate(low_cal_recs, 1):
        print(f"  {i}. {rec['name']} ({rec['calories']:.0f} cal) - {rec['score']:.2f}")
    print()


def main():
    """
    Main demo function.
    """
    print("="*70)
    print("  CS 125 Baseline Implementation Demo")
    print("  Personalized Nutrition Recommendation System")
    print("="*70)
    print()

    # ------------------------------------------------------------------ #
    # Step 1: Data ingestion pipeline                                     #
    #   A. Fetch UCI Dining Hall menus                                    #
    #   B. Upsert to Postgres                                             #
    #   C. Retrieve combined dataset from Postgres                        #
    # ------------------------------------------------------------------ #
    print("--- Step 1: Data Ingestion Pipeline ---\n")
    foods = demo_data_pipeline()
    if not foods:
        raise RuntimeError("No foods available to run demo.")
    print(f"Dataset ready: {len(foods)} foods loaded "
          f"({sum(1 for f in foods if f.source.startswith('uci_dining_'))} UCI dining, "
          f"{sum(1 for f in foods if f.source == 'usda_fdc')} USDA FDC).\n")

    # ------------------------------------------------------------------ #
    # Step 2: Scenario A — keyword search + top-k recommendations         #
    #         with per-food explanations                                  #
    # ------------------------------------------------------------------ #
    print("--- Step 2: Scenario A — keyword search & ranked recommendations ---\n")
    demo_indexing(foods)
    demo_ranking(foods)

    # ------------------------------------------------------------------ #
    # Step 3 & 4: Change context / user preference → show ranking change  #
    #             Scenario B — calorie-constrained second example         #
    # ------------------------------------------------------------------ #
    print("--- Step 3 & 4: Context change → ranking shift (Scenario B) ---")
    demo_context_awareness(foods)

    print("\n" + "="*70)
    print("  Demo Complete!")
    print("="*70)
    print("\nThis demo showed:")
    print("  ✓ Data ingestion (USDA FDC + UCI dining)")
    print("  ✓ Keyword and nutrient vector indexing")
    print("  ✓ Context-aware ranking algorithm")
    print("  ✓ Personalized recommendations with explanations")
    print()


if __name__ == "__main__":
    main()
