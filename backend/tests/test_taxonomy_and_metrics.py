"""
Tests for taxonomy helpers, deterministic dining IDs, and evaluation metrics.
"""
from src.evaluation.recommendation_metrics import (
    average_precision,
    intra_list_category_diversity,
    precision_at_k,
    recall_at_k,
)
from src.ingest.dininghall_sources import DiningMenuItem, UCIDiningScraper
from src.logical_view import Food
from src.taxonomy.food_taxonomy import filter_foods_by_facets, infer_food_category


def test_food_category_is_derived_on_creation():
    food = Food(1, "Greek Yogurt", 97.0, 10.0, 3.6, 5.0, 0.0)
    assert food.category == "dairy-eggs"
    assert food.taxonomy_path == ["food", "dairy-eggs"]


def test_filter_foods_by_facets_respects_category_and_tags():
    foods = [
        Food(1, "Grilled Chicken", 165, 31, 0, 3.6, 0, tags=["gluten-free"]),
        Food(2, "Garden Salad", 40, 2, 8, 1, 3, tags=["vegan", "vegetarian"]),
    ]

    filtered = filter_foods_by_facets(foods, category="vegetable", required_tags=["vegan"])

    assert [food.name for food in filtered] == ["Garden Salad"]


def test_dining_food_ids_are_deterministic_across_refreshes():
    scraper = UCIDiningScraper()
    items = [
        DiningMenuItem(
            name="Spicy Tofu Bowl",
            hall="Brandywine",
            meal_period="lunch",
            station="Wok",
            calories=320,
            protein=18,
            carbs=30,
            fat=12,
            fiber=5,
            dietary_flags=["vegan"],
        )
    ]

    first = scraper.convert_to_foods(items)[0]
    second = scraper.convert_to_foods(items)[0]

    assert first.food_id == second.food_id
    assert first.station == "Wok"
    assert first.hall == "Brandywine"
    assert first.meal_period == "lunch"


def test_precision_and_recall_at_k():
    recommended = [10, 20, 30, 40]
    relevant = {20, 40, 50}

    assert precision_at_k(recommended, relevant, 3) == 1 / 3
    assert recall_at_k(recommended, relevant, 4) == 2 / 3


def test_average_precision_and_diversity():
    recommended = [5, 7, 9, 11]
    relevant = {7, 11}

    assert average_precision(recommended, relevant) == 0.5
    assert intra_list_category_diversity(["protein", "protein", "fruit"]) == 2 / 3


def test_infer_food_category_covers_mixed_entree():
    assert infer_food_category("Roasted veggie quinoa bowl") == "grain-bread"
