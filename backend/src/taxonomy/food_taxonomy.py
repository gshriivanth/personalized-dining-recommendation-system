"""
Lightweight food taxonomy and facet filtering helpers.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence
import re


TAXONOMY_CATEGORIES: tuple[str, ...] = (
    "protein",
    "grain-bread",
    "fruit",
    "vegetable",
    "dairy-eggs",
    "beverage",
    "snack-sweets",
    "mixed-entree",
)

_TOKEN_GROUPS: dict[str, tuple[str, ...]] = {
    "protein": (
        "chicken", "beef", "pork", "steak", "turkey", "ham", "sausage",
        "salmon", "tuna", "fish", "shrimp", "tofu", "tempeh", "bean",
        "lentil", "egg", "eggs",
    ),
    "grain-bread": (
        "rice", "pasta", "quinoa", "bread", "bagel", "toast", "oat", "oatmeal",
        "cereal", "granola", "noodle", "tortilla", "bun",
    ),
    "fruit": (
        "apple", "banana", "orange", "berry", "berries", "grape", "melon",
        "mango", "pineapple", "peach", "pear", "avocado",
    ),
    "vegetable": (
        "broccoli", "spinach", "carrot", "lettuce", "cucumber", "pepper",
        "onion", "mushroom", "zucchini", "tomato", "salad", "vegetable",
    ),
    "dairy-eggs": (
        "milk", "yogurt", "cheese", "cream", "butter", "egg", "eggs",
    ),
    "beverage": (
        "juice", "tea", "coffee", "latte", "soda", "drink", "smoothie",
        "shake", "water",
    ),
    "snack-sweets": (
        "cookie", "brownie", "cake", "candy", "chip", "chips", "cracker",
        "dessert", "muffin", "bar", "trail mix", "popcorn", "ice cream",
    ),
}


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"\s+", " ", text)


def infer_food_category(name: str, tags: Optional[Sequence[str]] = None) -> str:
    """
    Infer a stable top-level category from the item's text and tags.
    """
    normalized_name = _normalize_text(name)
    words = set(normalized_name.split())
    normalized_tags = {_normalize_text(tag) for tag in (tags or [])}

    if normalized_tags & {"vegan", "vegetarian"} and any(
        token in normalized_name for token in ("salad", "vegetable", "broccoli", "spinach")
    ):
        return "vegetable"

    for category, tokens in _TOKEN_GROUPS.items():
        if any(
            (token in words) if " " not in token else (f" {token} " in f" {normalized_name} ")
            for token in tokens
        ):
            return category

    if len(normalized_name.split()) >= 3:
        return "mixed-entree"

    return "snack-sweets"


def taxonomy_path_for_category(category: str) -> List[str]:
    return ["food", category]


def filter_foods_by_facets(
    foods: Iterable,
    *,
    category: Optional[str] = None,
    required_tags: Optional[Sequence[str]] = None,
) -> List:
    """
    Filter foods by top-level category and required dietary tags.
    """
    normalized_category = category.lower() if category else None
    normalized_required_tags = {_normalize_text(tag) for tag in (required_tags or []) if tag}

    filtered = []
    for food in foods:
        food_category = getattr(food, "category", None) or infer_food_category(food.name, getattr(food, "tags", []))
        if normalized_category and food_category != normalized_category:
            continue

        food_tags = {_normalize_text(tag) for tag in getattr(food, "tags", [])}
        if normalized_required_tags and not normalized_required_tags.issubset(food_tags):
            continue

        filtered.append(food)

    return filtered
