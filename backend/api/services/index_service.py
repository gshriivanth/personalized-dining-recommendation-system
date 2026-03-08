# api/services/index_service.py
"""
Singleton wrapper around FoodIndexManager.
Built once at API startup via FastAPI lifespan, shared across all requests.
"""
from __future__ import annotations

import logging
from typing import Optional, List

from src.index.build_index import FoodIndexManager
from src.logical_view.food import Food

logger = logging.getLogger(__name__)

_index_manager: Optional[FoodIndexManager] = None


def get_index_manager() -> FoodIndexManager:
    """FastAPI dependency — returns the singleton index manager."""
    if _index_manager is None:
        raise RuntimeError("Index not built yet. Call build_index() during app lifespan.")
    return _index_manager


async def build_index(foods: List[Food]) -> None:
    """Called once during FastAPI lifespan startup."""
    global _index_manager
    logger.info("Building food index for %d foods...", len(foods))
    manager = FoodIndexManager()
    manager.build_index(foods)
    _index_manager = manager
    logger.info("Food index built successfully.")
