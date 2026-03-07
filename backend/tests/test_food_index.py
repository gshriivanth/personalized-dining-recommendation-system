# tests/test_food_index.py
"""
Tests for food indexing system.
"""
import pytest
from src.index import (
    tokenize,
    KeywordIndex,
    NutrientVectorIndex,
    FoodIndexManager
)
from src.logical_view import Food


class TestTokenize:
    """Tests for tokenization function."""

    def test_tokenize_simple(self):
        """Test tokenizing simple text."""
        tokens = tokenize("chicken breast")
        assert tokens == ["chicken", "breast"]

    def test_tokenize_with_punctuation(self):
        """Test tokenizing text with punctuation."""
        tokens = tokenize("Grilled, roasted chicken!")
        assert "grilled" in tokens
        assert "roasted" in tokens
        assert "chicken" in tokens

    def test_tokenize_lowercase(self):
        """Test that tokens are lowercased."""
        tokens = tokenize("CHICKEN BREAST")
        assert tokens == ["chicken", "breast"]

    def test_tokenize_numbers(self):
        """Test tokenizing text with numbers."""
        tokens = tokenize("Protein bar 20g")
        assert "protein" in tokens
        assert "bar" in tokens
        assert "20g" in tokens

    def test_tokenize_empty(self):
        """Test tokenizing empty string."""
        tokens = tokenize("")
        assert tokens == []


class TestKeywordIndex:
    """Tests for keyword inverted index."""

    def setup_method(self):
        """Set up test fixtures."""
        self.index = KeywordIndex()
        self.sample_foods = [
            Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0, brand="Tyson"),
            Food(2, "Grilled Chicken", 150, 30, 0, 3, 0),
            Food(3, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5),
            Food(4, "Chicken Rice Bowl", 200, 15, 30, 5, 2),
        ]

    def test_add_food(self):
        """Test adding a food to the index."""
        food = self.sample_foods[0]
        self.index.add_food(food)

        assert "chicken" in self.index.index
        assert "breast" in self.index.index
        assert 1 in self.index.index["chicken"]

    def test_add_multiple_foods(self):
        """Test adding multiple foods."""
        for food in self.sample_foods:
            self.index.add_food(food)

        # "chicken" should be in 3 foods
        assert len(self.index.index["chicken"]) == 3

    def test_search_single_term(self):
        """Test searching with single term."""
        for food in self.sample_foods:
            self.index.add_food(food)

        results = self.index.search("chicken")

        assert 1 in results  # Chicken Breast
        assert 2 in results  # Grilled Chicken
        assert 4 in results  # Chicken Rice Bowl
        assert 3 not in results  # Brown Rice

    def test_search_multiple_terms_or(self):
        """Test OR search with multiple terms."""
        for food in self.sample_foods:
            self.index.add_food(food)

        results = self.index.search("chicken rice")

        # Should match all foods containing either "chicken" or "rice"
        assert len(results) == 4

    def test_search_all_and(self):
        """Test AND search with multiple terms."""
        for food in self.sample_foods:
            self.index.add_food(food)

        results = self.index.search_all("chicken rice")

        # Should match only "Chicken Rice Bowl"
        assert 4 in results
        assert len(results) == 1

    def test_search_no_results(self):
        """Test search with no matching results."""
        for food in self.sample_foods:
            self.index.add_food(food)

        results = self.index.search("pizza")

        assert len(results) == 0

    def test_search_with_brand(self):
        """Test searching includes brand names."""
        self.index.add_food(self.sample_foods[0])

        results = self.index.search("tyson")

        assert 1 in results

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        for food in self.sample_foods:
            self.index.add_food(food)

        # Convert to dict
        data = self.index.to_dict()

        assert isinstance(data, dict)
        assert "chicken" in data
        assert isinstance(data["chicken"], list)

        # Load from dict
        new_index = KeywordIndex.from_dict(data)

        assert "chicken" in new_index.index
        assert new_index.index["chicken"] == self.index.index["chicken"]


class TestNutrientVectorIndex:
    """Tests for nutrient vector index."""

    def setup_method(self):
        """Set up test fixtures."""
        self.index = NutrientVectorIndex()
        self.sample_foods = [
            Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0, "lunch"),
            Food(2, "Grilled Chicken", 150, 30, 0, 3, 0, "lunch"),
            Food(3, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5, "any"),
            Food(4, "Scrambled Eggs", 155, 13, 1.1, 11, 0, "breakfast"),
        ]

    def test_add_food(self):
        """Test adding food to nutrient index."""
        food = self.sample_foods[0]
        self.index.add_food(food)

        assert 1 in self.index.foods
        assert self.index.foods[1] == food

    def test_get_food(self):
        """Test retrieving food by ID."""
        self.index.add_food(self.sample_foods[0])

        food = self.index.get_food(1)

        assert food is not None
        assert food.name == "Chicken Breast"

    def test_get_food_not_found(self):
        """Test retrieving non-existent food."""
        food = self.index.get_food(999)

        assert food is None

    def test_get_foods_multiple(self):
        """Test retrieving multiple foods."""
        for food in self.sample_foods:
            self.index.add_food(food)

        foods = self.index.get_foods({1, 3})

        assert len(foods) == 2
        assert any(f.food_id == 1 for f in foods)
        assert any(f.food_id == 3 for f in foods)

    def test_filter_by_meal_category(self):
        """Test filtering by meal category."""
        for food in self.sample_foods:
            self.index.add_food(food)

        lunch_foods = self.index.filter_by_meal_category("lunch")

        assert len(lunch_foods) >= 2  # At least 2 lunch items
        assert all(f.meal_category in ["lunch", "any"] for f in lunch_foods)

    def test_filter_by_meal_category_with_food_ids(self):
        """Test filtering specific foods by meal category."""
        for food in self.sample_foods:
            self.index.add_food(food)

        # Filter only foods 1 and 3 for lunch
        lunch_foods = self.index.filter_by_meal_category("lunch", {1, 3})

        assert len(lunch_foods) >= 1
        assert all(f.food_id in [1, 3] for f in lunch_foods)

    def test_filter_by_calorie_budget(self):
        """Test filtering by calorie budget."""
        for food in self.sample_foods:
            self.index.add_food(food)

        low_cal_foods = self.index.filter_by_calorie_budget(200.0)

        assert all(f.calories <= 200.0 for f in low_cal_foods)
        assert len(low_cal_foods) >= 2

    def test_filter_by_calorie_budget_specific_foods(self):
        """Test filtering specific foods by calorie budget."""
        for food in self.sample_foods:
            self.index.add_food(food)

        foods_to_filter = [self.sample_foods[0], self.sample_foods[2]]
        low_cal = self.index.filter_by_calorie_budget(200.0, foods_to_filter)

        assert all(f.calories <= 200.0 for f in low_cal)

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        for food in self.sample_foods:
            self.index.add_food(food)

        # Convert to dict
        data = self.index.to_dict()

        assert isinstance(data, dict)
        assert len(data) == len(self.sample_foods)

        # Load from dict
        new_index = NutrientVectorIndex.from_dict(data)

        assert len(new_index.foods) == len(self.index.foods)
        assert new_index.get_food(1).name == self.index.get_food(1).name


class TestFoodIndexManager:
    """Tests for FoodIndexManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = FoodIndexManager()
        self.sample_foods = [
            Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0, "lunch"),
            Food(2, "Grilled Chicken", 150, 30, 0, 3, 0, "lunch"),
            Food(3, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5, "any"),
            Food(4, "Scrambled Eggs", 155, 13, 1.1, 11, 0, "breakfast"),
        ]

    def test_build_index(self):
        """Test building both indexes."""
        self.manager.build_index(self.sample_foods)

        # Check keyword index
        assert "chicken" in self.manager.keyword_index.index

        # Check nutrient index
        assert 1 in self.manager.nutrient_index.foods

    def test_search_with_query_only(self):
        """Test search with text query only."""
        self.manager.build_index(self.sample_foods)

        results = self.manager.search(query="chicken")

        assert len(results) >= 2
        assert all("chicken" in f.name.lower() for f in results)

    def test_search_with_meal_type(self):
        """Test search with meal type filter."""
        self.manager.build_index(self.sample_foods)

        results = self.manager.search(meal_type="breakfast")

        assert len(results) >= 1
        assert all(f.meal_category in ["breakfast", "any"] for f in results)

    def test_search_with_calorie_budget(self):
        """Test search with calorie budget."""
        self.manager.build_index(self.sample_foods)

        results = self.manager.search(max_calories=200.0)

        assert all(f.calories <= 200.0 for f in results)

    def test_search_combined_filters(self):
        """Test search with multiple filters."""
        self.manager.build_index(self.sample_foods)

        results = self.manager.search(
            query="chicken",
            meal_type="lunch",
            max_calories=170.0
        )

        assert all("chicken" in f.name.lower() for f in results)
        assert all(f.meal_category in ["lunch", "any"] for f in results)
        assert all(f.calories <= 170.0 for f in results)

    def test_search_no_query(self):
        """Test search without query (returns all foods)."""
        self.manager.build_index(self.sample_foods)

        results = self.manager.search()

        assert len(results) == len(self.sample_foods)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
