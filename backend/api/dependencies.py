# api/dependencies.py
"""
FastAPI shared dependencies.
"""
from __future__ import annotations

from fastapi import Depends

from api.services.index_service import get_index_manager
from src.index.build_index import FoodIndexManager


def index_manager_dep() -> FoodIndexManager:
    """Dependency: returns the singleton in-memory index."""
    return get_index_manager()
