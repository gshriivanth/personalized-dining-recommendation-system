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

from src.logical_view import Food, UserGoals, ConsumedToday
from src.ingest.ingest_pipeline import DataIngestionPipeline
from src.config import USDA_FDC_API_KEY_ENV
from src.index import FoodIndexManager
from src.query.food_ranking import FoodRanker, RankingContext
from src.db import fetch_foods


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
    max_usda_foods: int = 50,
    foods_per_query: int = 10,
    max_queries: int = 2,
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


def demo_indexing(foods: list[Food]):
    """Demonstrate indexing functionality."""
    print("=== Building Indexes ===\n")

    manager = FoodIndexManager()
    manager.build_index(foods)

    print("\n=== Testing Keyword Search ===\n")

    # Test keyword search
    test_queries = ["chicken", "vegetarian", "protein"]

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
    print(f"\n  Remaining Targets:")
    print(f"    - Calories: {goals.calories - consumed.calories:.0f} kcal")
    print(f"    - Protein: {goals.protein - consumed.protein:.1f}g")
    print(f"    - Carbs: {goals.carbs - consumed.carbs:.1f}g")
    print(f"    - Fat: {goals.fat - consumed.fat:.1f}g")
    print(f"    - Fiber: {goals.fiber - consumed.fiber:.1f}g")

    # Use ingested foods as candidates
    candidate_foods = foods

    # Set up ranking context for lunch
    context = RankingContext(
        meal_type="lunch",
        time_of_day="afternoon",
        favorites={5, 6}  # Chicken and Salmon are favorites
    )

    print(f"\n  Context:")
    print(f"    - Meal Type: {context.meal_type}")
    print(f"    - Time of Day: {context.time_of_day}")
    print(f"    - Favorite Foods: {len(context.favorites)}")

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

    # Step 1: Load or ingest real data
    foods = load_or_ingest_foods()
    if not foods:
        raise RuntimeError("No foods available to run demo.")

    # Step 2: Demonstrate indexing
    index_manager = demo_indexing(foods)

    # Step 3: Demonstrate ranking
    demo_ranking(foods)

    # Step 4: Demonstrate context awareness
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
    print("Next steps:")
    print("  - Run tests: pytest tests/")
    print("  - Run full pipeline: python -m src.ingest.ingest_pipeline")
    print("  - Run ranking demo: python -m src.query.food_ranking")
    print()


if __name__ == "__main__":
    main()
