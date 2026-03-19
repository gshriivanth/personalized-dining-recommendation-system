"""
Taxonomy helpers for categorizing foods into stable, filterable groups.
"""

from src.taxonomy.food_taxonomy import (
    TAXONOMY_CATEGORIES,
    filter_foods_by_facets,
    infer_food_category,
    taxonomy_path_for_category,
)

__all__ = [
    "TAXONOMY_CATEGORIES",
    "filter_foods_by_facets",
    "infer_food_category",
    "taxonomy_path_for_category",
]
