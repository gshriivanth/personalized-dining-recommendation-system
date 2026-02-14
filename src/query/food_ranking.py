# src/query/food_ranking.py
"""
Nutrition-specific ranking algorithm for food recommendations.

Scores foods based on remaining nutrient targets, context bonuses, and
penalties for overshooting targets.
"""
from __future__ import annotations

from typing import List, Dict, Tuple, Optional, Set, Any, Iterable
from dataclasses import dataclass, field

from src.logical_view import Food, UserGoals, ConsumedToday


@dataclass
class RankingContext:
    """
    Context information for ranking foods.
    """
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    time_of_day: Optional[str] = None  # morning, afternoon, evening
    favorites: Set[int] = field(default_factory=set)  # Set of favorite food_ids


def filter_foods_by_source(
    foods: Iterable[Food],
    sources: Optional[Set[str]] = None,
    source_prefixes: Optional[List[str]] = None,
) -> List[Food]:
    """
    Filter foods by exact source or source prefix.

    If both sources and prefixes are provided, a food is included if it matches
    either condition.
    """
    if not sources and not source_prefixes:
        return list(foods)

    source_set = set(sources) if sources else set()
    prefixes = tuple(source_prefixes or [])

    filtered: List[Food] = []
    for food in foods:
        if source_set and food.source in source_set:
            filtered.append(food)
            continue
        if prefixes and any(food.source.startswith(prefix) for prefix in prefixes):
            filtered.append(food)
    return filtered


def calculate_remaining_targets(
    goals: UserGoals,
    consumed: ConsumedToday
) -> Dict[str, float]:
    """
    Calculate remaining nutrient targets for the day.

    Args:
        goals: User's daily nutrition goals
        consumed: Nutrients consumed so far today

    Returns:
        Dictionary of remaining targets (nutrient_name -> remaining_amount)
    """
    remaining = {}

    if goals.calories is not None:
        remaining['calories'] = max(0.0, goals.calories - consumed.calories)
    if goals.protein is not None:
        remaining['protein'] = max(0.0, goals.protein - consumed.protein)
    if goals.carbs is not None:
        remaining['carbs'] = max(0.0, goals.carbs - consumed.carbs)
    if goals.fat is not None:
        remaining['fat'] = max(0.0, goals.fat - consumed.fat)
    if goals.fiber is not None:
        remaining['fiber'] = max(0.0, goals.fiber - consumed.fiber)

    return remaining


def score_food(
    food: Food,
    remaining: Dict[str, float],
    context: RankingContext,
    serving_size: float = 100.0
) -> float:
    """
    Score a food based on how well it fits remaining nutrient targets.

    Scoring factors:
    1. Nutrient gap matching - foods that provide needed nutrients score higher
    2. Calorie constraint - heavy penalty for exceeding calorie budget
    3. Context bonus - boost for matching meal category
    4. User preference bonus - boost for favorite foods

    Args:
        food: Food to score
        remaining: Remaining nutrient targets
        context: Ranking context (meal type, favorites, etc.)
        serving_size: Serving size in grams (default 100g)

    Returns:
        Score value (higher is better)
    """
    score = 0.0
    multiplier = serving_size / 100.0

    # 1. Nutrient gap matching
    # Score positively if food provides needed nutrients without overshooting
    for nutrient in ['protein', 'carbs', 'fat', 'fiber']:
        if nutrient not in remaining:
            continue

        target_remaining = remaining[nutrient]
        if target_remaining <= 0:
            continue

        # Get food's nutrient value (scaled by serving size)
        food_nutrient = getattr(food, nutrient) * multiplier

        if food_nutrient > 0:
            if food_nutrient <= target_remaining:
                # Perfect: provides exactly what's needed
                # Score proportionally: closer to target = higher score
                score += (food_nutrient / target_remaining) * 10
            else:
                # Overshooting: still good but penalized
                overshoot = food_nutrient - target_remaining
                overshoot_penalty = (overshoot / target_remaining) * 2
                score += max(0, 5 - overshoot_penalty)

    # 2. Calorie constraint (hard constraint)
    if 'calories' in remaining:
        food_calories = food.calories * multiplier
        calorie_remaining = remaining['calories']

        if food_calories <= calorie_remaining:
            # Within budget - bonus for using available calories
            score += (food_calories / calorie_remaining) * 5
        else:
            # Over budget - heavy penalty
            overshoot_ratio = (food_calories - calorie_remaining) / calorie_remaining
            score -= 20 * (1 + overshoot_ratio)

    # 3. Context bonus: meal category match
    if context.meal_type and (food.meal_category == context.meal_type or
                              food.meal_category == 'any'):
        score += 5

    # 4. User preference bonus (if food in favorites)
    if food.food_id in context.favorites:
        score += 3

    return score


def rank_foods(
    candidate_foods: List[Food],
    goals: UserGoals,
    consumed: ConsumedToday,
    context: RankingContext,
    top_k: int = 10,
    serving_size: float = 100.0,
    sources: Optional[Set[str]] = None,
    source_prefixes: Optional[List[str]] = None,
) -> List[Tuple[Food, float]]:
    """
    Rank foods and return top-k recommendations.

    Args:
        candidate_foods: List of foods to rank
        goals: User's daily nutrition goals
        consumed: Nutrients consumed so far today
        context: Ranking context
        top_k: Number of top recommendations to return
        serving_size: Serving size in grams
        sources: Optional exact sources to include
        source_prefixes: Optional source prefixes to include

    Returns:
        List of (food, score) tuples, sorted by score descending
    """
    # Filter candidates by source if requested
    filtered_foods = filter_foods_by_source(
        candidate_foods,
        sources=sources,
        source_prefixes=source_prefixes,
    )

    # Calculate remaining targets
    remaining = calculate_remaining_targets(goals, consumed)

    # Score all foods
    scored_foods: List[Tuple[Food, float]] = []
    for food in filtered_foods:
        score = score_food(food, remaining, context, serving_size)
        scored_foods.append((food, score))

    # Sort by score descending
    scored_foods.sort(key=lambda x: x[1], reverse=True)

    # Return top-k
    return scored_foods[:top_k]


def generate_explanation(
    food: Food,
    remaining: Dict[str, float],
    context: RankingContext,
    serving_size: float = 100.0
) -> str:
    """
    Generate explanation for why a food was recommended.

    Args:
        food: Recommended food
        remaining: Remaining nutrient targets
        context: Ranking context
        serving_size: Serving size in grams

    Returns:
        Human-readable explanation string
    """
    explanations = []
    multiplier = serving_size / 100.0

    # Check which nutrients this food provides significantly
    significant_nutrients: List[str] = []

    for nutrient in ['protein', 'carbs', 'fat', 'fiber']:
        if nutrient not in remaining:
            continue

        target_remaining = remaining[nutrient]
        if target_remaining <= 0:
            continue

        food_nutrient = getattr(food, nutrient) * multiplier

        # If food provides >= 20% of remaining target, it's significant
        if food_nutrient >= target_remaining * 0.2:
            percentage = min(100, (food_nutrient / target_remaining) * 100)
            nutrient_name = nutrient.capitalize()
            explanations.append(
                f"{nutrient_name}: {food_nutrient:.1f}g "
                f"({percentage:.0f}% of remaining {target_remaining:.1f}g)"
            )

    # Add calorie info
    if 'calories' in remaining:
        food_calories = food.calories * multiplier
        calorie_remaining = remaining['calories']
        percentage = min(100, (food_calories / calorie_remaining) * 100)
        explanations.insert(0,
            f"Calories: {food_calories:.0f} kcal "
            f"({percentage:.0f}% of remaining {calorie_remaining:.0f} kcal)"
        )

    # Add context info
    if context.meal_type and food.meal_category == context.meal_type:
        explanations.append(f"Good for {context.meal_type}")

    if food.food_id in context.favorites:
        explanations.append("One of your favorites")

    if not explanations:
        explanations.append("Nutritionally balanced option")

    return "; ".join(explanations)


class FoodRanker:
    """
    Main ranking class that combines scoring and explanation generation.
    """

    def __init__(self):
        """Initialize ranker."""
        pass

    def recommend(
        self,
        candidate_foods: List[Food],
        goals: UserGoals,
        consumed: ConsumedToday,
        context: Optional[RankingContext] = None,
        top_k: int = 10,
        serving_size: float = 100.0,
        sources: Optional[Set[str]] = None,
        source_prefixes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate ranked food recommendations with explanations.

        Args:
        candidate_foods: List of foods to consider
        goals: User's daily nutrition goals
        consumed: Nutrients consumed so far today
        context: Ranking context
        top_k: Number of recommendations
        serving_size: Serving size in grams
        sources: Optional exact sources to include
        source_prefixes: Optional source prefixes to include

        Returns:
            List of dictionaries with food, score, and explanation
        """
        if context is None:
            context = RankingContext()

        # Rank foods
        ranked = rank_foods(
            candidate_foods,
            goals,
            consumed,
            context,
            top_k,
            serving_size,
            sources=sources,
            source_prefixes=source_prefixes,
        )

        # Calculate remaining targets for explanations
        remaining = calculate_remaining_targets(goals, consumed)

        # Generate recommendations with explanations
        recommendations = []
        for food, score in ranked:
            explanation = generate_explanation(food, remaining, context, serving_size)

            recommendations.append({
                'food': food,
                'score': score,
                'explanation': explanation,
                'food_id': food.food_id,
                'name': food.name,
                'calories': food.calories * (serving_size / 100.0),
                'protein': food.protein * (serving_size / 100.0),
                'carbs': food.carbs * (serving_size / 100.0),
                'fat': food.fat * (serving_size / 100.0),
                'fiber': food.fiber * (serving_size / 100.0),
            })

        return recommendations


def demo_ranking():
    """
    Demonstration of the ranking algorithm.
    """
    print("=== Food Ranking Algorithm Demo ===\n")

    # Create sample user goals
    goals = UserGoals(
        calories=2000.0,
        protein=150.0,
        carbs=200.0,
        fat=65.0,
        fiber=30.0
    )

    # Create sample consumed data (breakfast already eaten)
    consumed = ConsumedToday(
        calories=400.0,
        protein=20.0,
        carbs=50.0,
        fat=15.0,
        fiber=5.0
    )

    # Create sample foods
    sample_foods = [
        Food(1, "Grilled Chicken Breast", 165, 31, 0, 3.6, 0, "lunch", [], "Generic", "usda_fdc"),
        Food(2, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5, "any", [], "Generic", "usda_fdc"),
        Food(3, "Salmon Fillet", 206, 22, 0, 13, 0, "lunch", [], "Generic", "usda_fdc"),
        Food(4, "Broccoli", 34, 2.8, 7, 0.4, 2.6, "any", ["vegetarian"], "Generic", "usda_fdc"),
        Food(5, "Greek Yogurt", 97, 10, 3.6, 5, 0, "breakfast", [], "Generic", "usda_fdc"),
        Food(6, "Almonds", 579, 21, 22, 50, 12.5, "snack", [], "Generic", "usda_fdc"),
        Food(7, "Sweet Potato", 86, 1.6, 20, 0.1, 3, "any", [], "Generic", "usda_fdc"),
    ]

    # Create ranking context for lunch
    context = RankingContext(
        meal_type="lunch",
        time_of_day="afternoon",
        favorites={1, 3}  # Chicken and salmon are favorites
    )

    # Rank foods
    ranker = FoodRanker()
    recommendations = ranker.recommend(
        candidate_foods=sample_foods,
        goals=goals,
        consumed=consumed,
        context=context,
        top_k=5,
        serving_size=100.0
    )

    # Print results
    print("User Goals:")
    print(f"  Calories: {goals.calories} kcal")
    print(f"  Protein: {goals.protein}g")
    print(f"  Carbs: {goals.carbs}g")
    print(f"  Fat: {goals.fat}g")
    print(f"  Fiber: {goals.fiber}g")

    print("\nConsumed Today (Breakfast):")
    print(f"  Calories: {consumed.calories} kcal")
    print(f"  Protein: {consumed.protein}g")
    print(f"  Carbs: {consumed.carbs}g")
    print(f"  Fat: {consumed.fat}g")
    print(f"  Fiber: {consumed.fiber}g")

    remaining = calculate_remaining_targets(goals, consumed)
    print("\nRemaining Targets:")
    for nutrient, value in remaining.items():
        print(f"  {nutrient.capitalize()}: {value:.1f}")

    meal_label = (context.meal_type or "meal").capitalize()
    print(f"\n=== Top {len(recommendations)} Recommendations for {meal_label} ===\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} (Score: {rec['score']:.2f})")
        print(f"   {rec['explanation']}")
        print()


if __name__ == "__main__":
    demo_ranking()
