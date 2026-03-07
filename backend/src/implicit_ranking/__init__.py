# src/query/__init__.py
"""
Food ranking and query module.

Provides nutrition-specific ranking algorithms for personalized food recommendations.
"""

from src.implicit_ranking.food_ranking import (
    RankingContext,
    calculate_remaining_targets,
    score_food,
    rank_foods,
    generate_explanation,
    FoodRanker
)

__all__ = [
    "RankingContext",
    "calculate_remaining_targets",
    "score_food",
    "rank_foods",
    "generate_explanation",
    "FoodRanker"
]
