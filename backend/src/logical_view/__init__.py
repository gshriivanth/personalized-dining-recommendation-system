# src/logical_view/__init__.py
"""
Logical view / document data models for the nutrition recommendation system.

This package contains the core data structures representing:
- Food items (documents in IR terminology)
- User goals (nutrition targets)
- Consumed nutrients (daily tracking)
"""

from src.logical_view.food import Food
from src.logical_view.user_goals import UserGoals
from src.logical_view.consumed_today import ConsumedToday

__all__ = ["Food", "UserGoals", "ConsumedToday"]
