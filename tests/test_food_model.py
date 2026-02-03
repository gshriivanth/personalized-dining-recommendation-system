# tests/test_food_model.py
"""
Unit tests for Food model and related classes.
"""
import pytest
from src.logical_view import Food, UserGoals, ConsumedToday


class TestFood:
    """Tests for Food dataclass."""

    def test_food_creation(self):
        """Test creating a Food object with all fields."""
        food = Food(
            food_id=123,
            name="Chicken Breast",
            calories=165.0,
            protein=31.0,
            carbs=0.0,
            fat=3.6,
            fiber=0.0,
            meal_category="lunch",
            tags=["high-protein"],
            brand="Generic",
            source="usda_fdc"
        )

        assert food.food_id == 123
        assert food.name == "Chicken Breast"
        assert food.calories == 165.0
        assert food.protein == 31.0
        assert food.meal_category == "lunch"
        assert "high-protein" in food.tags

    def test_food_defaults(self):
        """Test Food object with default values."""
        food = Food(
            food_id=1,
            name="Test Food",
            calories=100.0,
            protein=10.0,
            carbs=15.0,
            fat=5.0,
            fiber=2.0
        )

        assert food.meal_category == "any"
        assert food.tags == []
        assert food.brand == ""
        assert food.source == "usda_fdc"

    def test_food_to_dict(self):
        """Test converting Food to dictionary."""
        food = Food(
            food_id=1,
            name="Apple",
            calories=52.0,
            protein=0.3,
            carbs=14.0,
            fat=0.2,
            fiber=2.4,
            tags=["vegetarian", "vegan"]
        )

        data = food.to_dict()

        assert data["food_id"] == 1
        assert data["name"] == "Apple"
        assert data["calories"] == 52.0
        assert data["tags"] == ["vegetarian", "vegan"]

    def test_food_from_dict(self):
        """Test creating Food from dictionary."""
        data = {
            "food_id": 2,
            "name": "Banana",
            "calories": 89.0,
            "protein": 1.1,
            "carbs": 23.0,
            "fat": 0.3,
            "fiber": 2.6,
            "meal_category": "snack",
            "tags": ["vegan"],
            "brand": "Dole",
            "source": "usda_fdc"
        }

        food = Food.from_dict(data)

        assert food.food_id == 2
        assert food.name == "Banana"
        assert food.calories == 89.0
        assert food.meal_category == "snack"

    def test_get_nutrient_vector(self):
        """Test getting nutrient vector."""
        food = Food(
            food_id=1,
            name="Test",
            calories=200.0,
            protein=20.0,
            carbs=30.0,
            fat=10.0,
            fiber=5.0
        )

        vector = food.get_nutrient_vector()

        assert vector == [200.0, 20.0, 30.0, 10.0, 5.0]

    def test_food_str_representation(self):
        """Test string representation."""
        food = Food(
            food_id=1,
            name="Salmon",
            calories=206.0,
            protein=22.0,
            carbs=0.0,
            fat=13.0,
            fiber=0.0
        )

        str_repr = str(food)

        assert "Salmon" in str_repr
        assert "206.0" in str_repr


class TestUserGoals:
    """Tests for UserGoals dataclass."""

    def test_user_goals_creation(self):
        """Test creating UserGoals with all fields."""
        goals = UserGoals(
            calories=2000.0,
            protein=150.0,
            carbs=200.0,
            fat=65.0,
            fiber=30.0
        )

        assert goals.calories == 2000.0
        assert goals.protein == 150.0
        assert goals.carbs == 200.0
        assert goals.fat == 65.0
        assert goals.fiber == 30.0

    def test_user_goals_partial(self):
        """Test creating UserGoals with some optional fields."""
        goals = UserGoals(
            calories=2000.0,
            protein=150.0
        )

        assert goals.calories == 2000.0
        assert goals.protein == 150.0
        assert goals.carbs is None
        assert goals.fat is None
        assert goals.fiber is None

    def test_user_goals_to_dict(self):
        """Test converting UserGoals to dictionary."""
        goals = UserGoals(calories=1800.0, protein=120.0)
        data = goals.to_dict()

        assert data["calories"] == 1800.0
        assert data["protein"] == 120.0
        assert data["carbs"] is None

    def test_user_goals_from_dict(self):
        """Test creating UserGoals from dictionary."""
        data = {
            "calories": 2200.0,
            "protein": 180.0,
            "carbs": 250.0,
            "fat": 70.0,
            "fiber": 35.0
        }

        goals = UserGoals.from_dict(data)

        assert goals.calories == 2200.0
        assert goals.protein == 180.0


class TestConsumedToday:
    """Tests for ConsumedToday dataclass."""

    def test_consumed_today_defaults(self):
        """Test default values for ConsumedToday."""
        consumed = ConsumedToday()

        assert consumed.calories == 0.0
        assert consumed.protein == 0.0
        assert consumed.carbs == 0.0
        assert consumed.fat == 0.0
        assert consumed.fiber == 0.0

    def test_consumed_today_with_values(self):
        """Test creating ConsumedToday with values."""
        consumed = ConsumedToday(
            calories=500.0,
            protein=30.0,
            carbs=60.0,
            fat=15.0,
            fiber=8.0
        )

        assert consumed.calories == 500.0
        assert consumed.protein == 30.0

    def test_add_food_100g(self):
        """Test adding a food with default 100g serving."""
        consumed = ConsumedToday()

        food = Food(
            food_id=1,
            name="Chicken",
            calories=165.0,
            protein=31.0,
            carbs=0.0,
            fat=3.6,
            fiber=0.0
        )

        consumed.add_food(food, serving_size=100.0)

        assert consumed.calories == 165.0
        assert consumed.protein == 31.0
        assert consumed.fat == 3.6

    def test_add_food_custom_serving(self):
        """Test adding a food with custom serving size."""
        consumed = ConsumedToday()

        food = Food(
            food_id=1,
            name="Rice",
            calories=370.0,  # per 100g
            protein=7.9,
            carbs=77.2,
            fat=2.9,
            fiber=3.5
        )

        # Add 50g serving (half)
        consumed.add_food(food, serving_size=50.0)

        assert consumed.calories == pytest.approx(185.0)
        assert consumed.protein == pytest.approx(3.95)
        assert consumed.carbs == pytest.approx(38.6)

    def test_add_multiple_foods(self):
        """Test adding multiple foods."""
        consumed = ConsumedToday()

        food1 = Food(1, "Food1", 100.0, 10.0, 15.0, 5.0, 2.0)
        food2 = Food(2, "Food2", 200.0, 20.0, 25.0, 10.0, 3.0)

        consumed.add_food(food1, 100.0)
        consumed.add_food(food2, 100.0)

        assert consumed.calories == 300.0
        assert consumed.protein == 30.0
        assert consumed.carbs == 40.0
        assert consumed.fat == 15.0
        assert consumed.fiber == 5.0

    def test_to_dict(self):
        """Test converting ConsumedToday to dictionary."""
        consumed = ConsumedToday(
            calories=400.0,
            protein=25.0,
            carbs=50.0,
            fat=12.0,
            fiber=6.0
        )

        data = consumed.to_dict()

        assert data["calories"] == 400.0
        assert data["protein"] == 25.0
        assert data["carbs"] == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
