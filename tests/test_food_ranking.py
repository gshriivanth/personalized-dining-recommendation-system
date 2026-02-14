# tests/test_food_ranking.py
"""
Tests for food ranking algorithm.
"""
import pytest
from src.query.food_ranking import (
    calculate_remaining_targets,
    score_food,
    rank_foods,
    generate_explanation,
    RankingContext,
    FoodRanker
)
from src.logical_view import Food, UserGoals, ConsumedToday


class TestCalculateRemainingTargets:
    """Tests for calculating remaining nutrient targets."""

    def test_calculate_remaining_all_nutrients(self):
        """Test calculating remaining with all nutrients."""
        goals = UserGoals(
            calories=2000.0,
            protein=150.0,
            carbs=200.0,
            fat=65.0,
            fiber=30.0
        )
        consumed = ConsumedToday(
            calories=500.0,
            protein=30.0,
            carbs=50.0,
            fat=15.0,
            fiber=5.0
        )

        remaining = calculate_remaining_targets(goals, consumed)

        assert remaining['calories'] == 1500.0
        assert remaining['protein'] == 120.0
        assert remaining['carbs'] == 150.0
        assert remaining['fat'] == 50.0
        assert remaining['fiber'] == 25.0

    def test_calculate_remaining_partial_goals(self):
        """Test with partial goals."""
        goals = UserGoals(
            calories=2000.0,
            protein=150.0
        )
        consumed = ConsumedToday(
            calories=800.0,
            protein=40.0
        )

        remaining = calculate_remaining_targets(goals, consumed)

        assert remaining['calories'] == 1200.0
        assert remaining['protein'] == 110.0
        assert 'carbs' not in remaining

    def test_calculate_remaining_zero_or_negative(self):
        """Test when consumed exceeds goals."""
        goals = UserGoals(
            calories=2000.0,
            protein=150.0
        )
        consumed = ConsumedToday(
            calories=2100.0,
            protein=160.0
        )

        remaining = calculate_remaining_targets(goals, consumed)

        assert remaining['calories'] == 0.0
        assert remaining['protein'] == 0.0


class TestScoreFood:
    """Tests for food scoring function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.remaining = {
            'calories': 1500.0,
            'protein': 120.0,
            'carbs': 150.0,
            'fat': 50.0,
            'fiber': 25.0
        }
        self.context = RankingContext()

    def test_score_food_perfect_match(self):
        """Test scoring food that fits perfectly."""
        food = Food(
            1, "Chicken Breast",
            calories=165.0,  # per 100g
            protein=31.0,
            carbs=0.0,
            fat=3.6,
            fiber=0.0,
            meal_category="lunch"
        )

        score = score_food(food, self.remaining, self.context, serving_size=100.0)

        assert score > 0

    def test_score_food_within_calorie_budget(self):
        """Test that food within budget scores positively."""
        food = Food(
            1, "Apple",
            calories=52.0,
            protein=0.3,
            carbs=14.0,
            fat=0.2,
            fiber=2.4
        )

        score = score_food(food, self.remaining, self.context)

        assert score > 0

    def test_score_food_exceeds_calorie_budget(self):
        """Test that food exceeding budget is penalized."""
        food = Food(
            1, "High Cal Food",
            calories=2000.0,  # Exceeds remaining 1500
            protein=10.0,
            carbs=20.0,
            fat=10.0,
            fiber=5.0
        )

        score = score_food(food, self.remaining, self.context)

        assert score < 0  # Should be negative due to calorie penalty

    def test_score_food_meal_category_bonus(self):
        """Test meal category matching bonus."""
        context_lunch = RankingContext(meal_type="lunch")

        food_lunch = Food(1, "Lunch Food", 100, 10, 15, 5, 2, meal_category="lunch")
        food_breakfast = Food(2, "Breakfast Food", 100, 10, 15, 5, 2, meal_category="breakfast")

        score_match = score_food(food_lunch, self.remaining, context_lunch)
        score_no_match = score_food(food_breakfast, self.remaining, context_lunch)

        assert score_match > score_no_match

    def test_score_food_favorites_bonus(self):
        """Test favorites bonus."""
        context_with_fav = RankingContext(favorites={1})
        context_without_fav = RankingContext()

        food = Food(1, "Favorite Food", 100, 10, 15, 5, 2)

        score_fav = score_food(food, self.remaining, context_with_fav)
        score_no_fav = score_food(food, self.remaining, context_without_fav)

        assert score_fav > score_no_fav

    def test_score_food_custom_serving_size(self):
        """Test scoring with custom serving size."""
        food = Food(1, "Test Food", 200, 20, 30, 10, 5)

        score_100g = score_food(food, self.remaining, self.context, serving_size=100.0)
        score_50g = score_food(food, self.remaining, self.context, serving_size=50.0)

        # 50g serving should have different score than 100g
        assert score_100g != score_50g


class TestRankFoods:
    """Tests for ranking multiple foods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.goals = UserGoals(
            calories=2000.0,
            protein=150.0,
            carbs=200.0,
            fat=65.0,
            fiber=30.0
        )
        self.consumed = ConsumedToday(
            calories=500.0,
            protein=20.0,
            carbs=50.0,
            fat=15.0,
            fiber=5.0
        )
        self.context = RankingContext(meal_type="lunch")

        self.sample_foods = [
            Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0, "lunch"),
            Food(2, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5, "any"),
            Food(3, "Salmon", 206, 22, 0, 13, 0, "lunch"),
            Food(4, "Broccoli", 34, 2.8, 7, 0.4, 2.6, "any"),
            Food(5, "Almonds", 579, 21, 22, 50, 12.5, "snack"),
        ]

    def test_rank_foods_basic(self):
        """Test basic ranking functionality."""
        ranked = rank_foods(
            self.sample_foods,
            self.goals,
            self.consumed,
            self.context,
            top_k=3
        )

        assert len(ranked) == 3
        assert all(isinstance(item, tuple) for item in ranked)
        assert all(isinstance(item[0], Food) for item in ranked)
        assert all(isinstance(item[1], (int, float)) for item in ranked)

    def test_rank_foods_sorted_descending(self):
        """Test that foods are sorted by score descending."""
        ranked = rank_foods(
            self.sample_foods,
            self.goals,
            self.consumed,
            self.context,
            top_k=5
        )

        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_foods_top_k(self):
        """Test that only top-k foods are returned."""
        ranked = rank_foods(
            self.sample_foods,
            self.goals,
            self.consumed,
            self.context,
            top_k=2
        )

        assert len(ranked) == 2

    def test_rank_foods_high_protein_preferred(self):
        """Test that high-protein foods rank higher when protein needed."""
        # Set consumed to need more protein
        consumed_low_protein = ConsumedToday(
            calories=500.0,
            protein=10.0,  # Very low protein consumed
            carbs=50.0,
            fat=15.0,
            fiber=5.0
        )

        ranked = rank_foods(
            self.sample_foods,
            self.goals,
            consumed_low_protein,
            self.context,
            top_k=5
        )

        # Chicken and Salmon (high protein) should be near the top
        top_foods = [food.name for food, _ in ranked[:2]]
        assert any(name in top_foods for name in ["Chicken Breast", "Salmon"])

    def test_rank_foods_source_filter_exact(self):
        """Test filtering by exact source."""
        foods = [
            Food(1, "USDA Food", 100, 10, 10, 5, 2, source="usda_fdc"),
            Food(2, "UCI Food", 100, 10, 10, 5, 2, source="uci_dining_brandywine"),
        ]

        ranked = rank_foods(
            foods,
            self.goals,
            self.consumed,
            self.context,
            sources={"usda_fdc"},
            top_k=5,
        )

        assert len(ranked) == 1
        assert ranked[0][0].source == "usda_fdc"

    def test_rank_foods_source_filter_prefix(self):
        """Test filtering by source prefix."""
        foods = [
            Food(1, "USDA Food", 100, 10, 10, 5, 2, source="usda_fdc"),
            Food(2, "UCI Food", 100, 10, 10, 5, 2, source="uci_dining_anteatery"),
        ]

        ranked = rank_foods(
            foods,
            self.goals,
            self.consumed,
            self.context,
            source_prefixes=["uci_dining_"],
            top_k=5,
        )

        assert len(ranked) == 1
        assert ranked[0][0].source.startswith("uci_dining_")


class TestGenerateExplanation:
    """Tests for explanation generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.remaining = {
            'calories': 1500.0,
            'protein': 120.0,
            'carbs': 150.0,
            'fat': 50.0,
            'fiber': 25.0
        }
        self.context = RankingContext()

    def test_generate_explanation_basic(self):
        """Test basic explanation generation."""
        food = Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0)

        explanation = generate_explanation(food, self.remaining, self.context)

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "Calories" in explanation

    def test_generate_explanation_high_protein(self):
        """Test explanation highlights significant nutrients."""
        food = Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0)

        explanation = generate_explanation(food, self.remaining, self.context)

        # Should mention protein since it's significant
        assert "Protein" in explanation

    def test_generate_explanation_meal_category(self):
        """Test explanation includes meal category match."""
        context_lunch = RankingContext(meal_type="lunch")
        food = Food(1, "Lunch Food", 100, 10, 15, 5, 2, meal_category="lunch")

        explanation = generate_explanation(food, self.remaining, context_lunch)

        assert "lunch" in explanation.lower()

    def test_generate_explanation_favorite(self):
        """Test explanation mentions favorites."""
        context_with_fav = RankingContext(favorites={1})
        food = Food(1, "Favorite", 100, 10, 15, 5, 2)

        explanation = generate_explanation(food, self.remaining, context_with_fav)

        assert "favorite" in explanation.lower()


class TestFoodRanker:
    """Tests for FoodRanker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = FoodRanker()
        self.goals = UserGoals(calories=2000.0, protein=150.0)
        self.consumed = ConsumedToday(calories=500.0, protein=30.0)
        self.sample_foods = [
            Food(1, "Chicken", 165, 31, 0, 3.6, 0),
            Food(2, "Rice", 370, 7.9, 77.2, 2.9, 3.5),
        ]

    def test_ranker_initialization(self):
        """Test ranker initialization."""
        assert self.ranker is not None

    def test_recommend_returns_list(self):
        """Test that recommend returns a list."""
        recommendations = self.ranker.recommend(
            self.sample_foods,
            self.goals,
            self.consumed
        )

        assert isinstance(recommendations, list)

    def test_recommend_dict_structure(self):
        """Test recommendation dictionary structure."""
        recommendations = self.ranker.recommend(
            self.sample_foods,
            self.goals,
            self.consumed,
            top_k=1
        )

        assert len(recommendations) == 1
        rec = recommendations[0]

        assert 'food' in rec
        assert 'score' in rec
        assert 'explanation' in rec
        assert 'food_id' in rec
        assert 'name' in rec
        assert 'calories' in rec
        assert 'protein' in rec

    def test_recommend_with_context(self):
        """Test recommendations with context."""
        context = RankingContext(meal_type="lunch", favorites={1})

        recommendations = self.ranker.recommend(
            self.sample_foods,
            self.goals,
            self.consumed,
            context=context
        )

        assert len(recommendations) > 0

    def test_recommend_custom_serving_size(self):
        """Test recommendations with custom serving size."""
        recommendations = self.ranker.recommend(
            self.sample_foods,
            self.goals,
            self.consumed,
            serving_size=150.0  # 150g serving
        )

        # Nutrient values should be scaled to 150g
        rec = recommendations[0]
        food = rec['food']

        # Check that returned calories are scaled
        expected_calories = food.calories * 1.5
        assert rec['calories'] == pytest.approx(expected_calories)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
