# tests/test_ingestion_pipeline.py
"""
Tests for data ingestion pipeline.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ingest.ingest_pipeline import (
    get_nutrient_value,
    parse_usda_food,
    infer_meal_category,
    infer_dietary_tags,
    DataIngestionPipeline
)
from src.logical_view import Food


class TestNutrientExtraction:
    """Tests for nutrient extraction from USDA data."""

    def test_get_nutrient_value_found(self):
        """Test extracting nutrient that exists."""
        food_data = {
            "foodNutrients": [
                {"nutrientId": 1008, "amount": 165.0},
                {"nutrientId": 1003, "amount": 31.0}
            ]
        }

        calories = get_nutrient_value(food_data, 1008)
        protein = get_nutrient_value(food_data, 1003)

        assert calories == 165.0
        assert protein == 31.0

    def test_get_nutrient_value_not_found(self):
        """Test extracting nutrient that doesn't exist."""
        food_data = {
            "foodNutrients": [
                {"nutrientId": 1008, "amount": 100.0}
            ]
        }

        fiber = get_nutrient_value(food_data, 1079)

        assert fiber == 0.0

    def test_get_nutrient_value_nested_structure(self):
        """Test extracting nutrient from nested structure."""
        food_data = {
            "foodNutrients": [
                {
                    "nutrient": {"id": 1008},
                    "amount": 200.0
                }
            ]
        }

        calories = get_nutrient_value(food_data, 1008)

        assert calories == 200.0


class TestFoodParsing:
    """Tests for parsing USDA food data."""

    def test_parse_usda_food_success(self):
        """Test parsing valid USDA food data."""
        food_data = {
            "fdcId": 12345,
            "description": "Chicken breast, roasted",
            "brandOwner": "Generic",
            "foodNutrients": [
                {"nutrientId": 1008, "amount": 165.0},  # calories
                {"nutrientId": 1003, "amount": 31.0},   # protein
                {"nutrientId": 1005, "amount": 0.0},    # carbs
                {"nutrientId": 1004, "amount": 3.6},    # fat
                {"nutrientId": 1079, "amount": 0.0}     # fiber
            ]
        }

        food = parse_usda_food(food_data)

        assert food is not None
        assert food.food_id == 12345
        assert food.name == "Chicken breast, roasted"
        assert food.calories == 165.0
        assert food.protein == 31.0
        assert food.source == "usda_fdc"

    def test_parse_usda_food_no_nutrients(self):
        """Test parsing food with no nutritional data."""
        food_data = {
            "fdcId": 123,
            "description": "Empty Food",
            "foodNutrients": []
        }

        food = parse_usda_food(food_data)

        assert food is None

    def test_parse_usda_food_missing_fdc_id(self):
        """Test parsing food without FDC ID."""
        food_data = {
            "description": "Test Food",
            "foodNutrients": [
                {"nutrientId": 1008, "amount": 100.0}
            ]
        }

        food = parse_usda_food(food_data)

        assert food is None

    def test_parse_usda_food_with_error(self):
        """Test parsing malformed food data."""
        food_data = {}  # Invalid structure

        food = parse_usda_food(food_data)

        assert food is None


class TestMealCategoryInference:
    """Tests for meal category inference."""

    def test_infer_breakfast(self):
        """Test inferring breakfast category."""
        assert infer_meal_category("Scrambled eggs") == "breakfast"
        assert infer_meal_category("Oatmeal with fruit") == "breakfast"
        assert infer_meal_category("Pancakes") == "breakfast"

    def test_infer_snack(self):
        """Test inferring snack category."""
        assert infer_meal_category("Potato chips") == "snack"
        assert infer_meal_category("Chocolate chip cookie") == "snack"
        assert infer_meal_category("Mixed nuts") == "snack"

    def test_infer_lunch(self):
        """Test inferring lunch/dinner category."""
        assert infer_meal_category("Grilled chicken") == "lunch"
        assert infer_meal_category("Salmon fillet") == "lunch"
        assert infer_meal_category("Beef steak") == "lunch"

    def test_infer_any(self):
        """Test inferring 'any' category for generic foods."""
        assert infer_meal_category("Broccoli") == "any"
        assert infer_meal_category("Brown rice") == "any"
        assert infer_meal_category("Apple") == "any"


class TestDietaryTagsInference:
    """Tests for dietary tags inference."""

    def test_infer_vegan(self):
        """Test inferring vegan tag."""
        tags = infer_dietary_tags("Vegan protein shake")
        assert "vegan" in tags
        assert "vegetarian" in tags

    def test_infer_vegetarian(self):
        """Test inferring vegetarian tag."""
        tags = infer_dietary_tags("Vegetarian burger")
        assert "vegetarian" in tags

    def test_infer_gluten_free(self):
        """Test inferring gluten-free tag."""
        tags = infer_dietary_tags("Gluten-free bread")
        assert "gluten-free" in tags

    def test_infer_multiple_tags(self):
        """Test inferring multiple tags."""
        tags = infer_dietary_tags("Organic vegan gluten free pasta")
        assert "vegan" in tags
        assert "vegetarian" in tags
        assert "gluten-free" in tags
        assert "organic" in tags

    def test_infer_no_tags(self):
        """Test food with no special tags."""
        tags = infer_dietary_tags("Regular chicken breast")
        assert tags == []


class TestDataIngestionPipeline:
    """Tests for DataIngestionPipeline class."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = DataIngestionPipeline()

        assert pipeline.usda_client is not None
        assert pipeline.uci_scraper is not None
        assert pipeline.foods == []

    @patch('src.ingest.ingest_pipeline.USDAFoodDataCentralClient')
    def test_fetch_usda_foods(self, mock_client_class):
        """Test fetching USDA foods."""
        # Mock the API response
        mock_client = Mock()
        mock_client.search_foods.return_value = {
            "foods": [
                {
                    "fdcId": 1,
                    "description": "Test Food 1",
                    "foodNutrients": [
                        {"nutrientId": 1008, "amount": 100.0},
                        {"nutrientId": 1003, "amount": 10.0},
                        {"nutrientId": 1005, "amount": 15.0},
                        {"nutrientId": 1004, "amount": 5.0},
                        {"nutrientId": 1079, "amount": 2.0}
                    ]
                }
            ]
        }
        mock_client_class.return_value = mock_client

        pipeline = DataIngestionPipeline()
        foods = pipeline.fetch_usda_foods(max_foods=1, foods_per_query=10, delay_seconds=0)

        assert len(foods) >= 1
        # Note: Actual count may vary based on query results

    @patch('src.ingest.ingest_pipeline.UCIDiningScraper')
    def test_fetch_uci_dining_foods(self, mock_scraper_class):
        """Test fetching UCI dining foods."""
        # Mock the scraper
        mock_scraper = Mock()
        mock_scraper.scrape_all_halls.return_value = {
            "Brandywine": [],
            "Anteatery": []
        }
        mock_scraper.convert_to_foods.return_value = []
        mock_scraper_class.return_value = mock_scraper

        pipeline = DataIngestionPipeline()
        foods = pipeline.fetch_uci_dining_foods()

        assert isinstance(foods, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
