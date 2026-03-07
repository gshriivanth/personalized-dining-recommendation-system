# tests/test_food_ranking.py
"""
Tests for food ranking algorithm.
"""
import pytest
from src.implicit_ranking.food_ranking import (
    calculate_remaining_targets,
    get_meals_remaining,
    score_food,
    rank_foods,
    generate_explanation,
    RankingContext,
    FoodRanker,
    NUTRIENT_WEIGHTS,
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


class TestGetMealsRemaining:
    """Tests for the meals-remaining helper."""

    def test_morning_returns_3(self):
        assert get_meals_remaining(RankingContext(time_of_day="morning")) == 3

    def test_breakfast_meal_type_returns_3(self):
        assert get_meals_remaining(RankingContext(meal_type="breakfast")) == 3

    def test_afternoon_returns_2(self):
        assert get_meals_remaining(RankingContext(time_of_day="afternoon")) == 2

    def test_lunch_meal_type_returns_2(self):
        assert get_meals_remaining(RankingContext(meal_type="lunch")) == 2

    def test_evening_returns_1(self):
        assert get_meals_remaining(RankingContext(time_of_day="evening")) == 1

    def test_dinner_meal_type_returns_1(self):
        assert get_meals_remaining(RankingContext(meal_type="dinner")) == 1

    def test_no_context_defaults_to_2(self):
        assert get_meals_remaining(RankingContext()) == 2

    def test_time_of_day_takes_priority_over_snack(self):
        # snack meal_type with no time_of_day → defaults to 2
        assert get_meals_remaining(RankingContext(meal_type="snack")) == 2


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

    def test_score_food_per_meal_calorie_penalty(self):
        """Food consuming the full daily budget is penalised when split across 2 meals."""
        # A food with exactly the total remaining calories should overshoot the per-meal
        # budget when meals_remaining=2 and therefore score lower than with meals_remaining=1.
        food = Food(1, "Big Meal", 1500, 10, 20, 10, 5)

        score_one_meal = score_food(food, self.remaining, self.context,
                                    serving_size=100.0, meals_remaining=1)
        score_two_meals = score_food(food, self.remaining, self.context,
                                     serving_size=100.0, meals_remaining=2)

        # With 2 meals left the per-meal budget is 750 kcal; the 1500 kcal food
        # overshoots and must be penalised relative to the single-meal scenario.
        assert score_two_meals < score_one_meal

    def test_score_food_protein_weighted_higher(self):
        """Verify that protein has a higher scoring weight than carbs."""
        assert NUTRIENT_WEIGHTS['protein'] > NUTRIENT_WEIGHTS['carbs']

        # A food that fills the protein target should outscore an otherwise
        # identical food that fills only the carbs target.
        remaining = {'calories': 800.0, 'protein': 50.0, 'carbs': 50.0, 'fat': 0.0, 'fiber': 0.0}
        protein_food = Food(1, "Protein Food", 100, 50, 0, 0, 0)   # fills protein target
        carb_food    = Food(2, "Carb Food",    100,  0, 50, 0, 0)   # fills carbs target

        ctx = RankingContext()
        score_protein = score_food(protein_food, remaining, ctx, meals_remaining=1)
        score_carb    = score_food(carb_food,    remaining, ctx, meals_remaining=1)

        assert score_protein > score_carb


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

        # Chicken and Salmon (high protein, matching meal category) should appear
        # in the top 3 thanks to the elevated protein weight.
        top_foods = [food.name for food, _ in ranked[:3]]
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

    def test_generate_explanation_references_meal_target(self):
        """Explanation percentages should be relative to per-meal targets."""
        food = Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0)

        explanation = generate_explanation(food, self.remaining, self.context,
                                           meals_remaining=2)

        assert "meal target" in explanation

    def test_generate_explanation_per_meal_percentage_differs_from_daily(self):
        """Percentage shown should reflect the per-meal budget, not the full daily remaining."""
        food = Food(1, "Test Food", 500, 10, 10, 5, 2)
        remaining = {'calories': 1000.0}

        # With 2 meals remaining the per-meal budget is 500 kcal → 100%
        explanation_2 = generate_explanation(food, remaining, self.context, meals_remaining=2)
        # With 1 meal remaining the per-meal budget is 1000 kcal → 50%
        explanation_1 = generate_explanation(food, remaining, self.context, meals_remaining=1)

        assert "100%" in explanation_2
        assert "50%" in explanation_1


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
