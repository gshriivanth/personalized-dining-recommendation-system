"""
Offline evaluation metrics for recommendation experiments.
"""
from __future__ import annotations

from typing import Iterable, Sequence


def precision_at_k(recommended_ids: Sequence[int], relevant_ids: Iterable[int], k: int) -> float:
    if k <= 0:
        return 0.0
    relevant = set(relevant_ids)
    if not recommended_ids:
        return 0.0
    top_k = list(recommended_ids[:k])
    if not top_k:
        return 0.0
    hits = sum(1 for item_id in top_k if item_id in relevant)
    return hits / len(top_k)


def recall_at_k(recommended_ids: Sequence[int], relevant_ids: Iterable[int], k: int) -> float:
    relevant = set(relevant_ids)
    if not relevant or k <= 0:
        return 0.0
    top_k = list(recommended_ids[:k])
    hits = sum(1 for item_id in top_k if item_id in relevant)
    return hits / len(relevant)


def average_precision(recommended_ids: Sequence[int], relevant_ids: Iterable[int], k: int | None = None) -> float:
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0

    ranked = list(recommended_ids if k is None else recommended_ids[:k])
    if not ranked:
        return 0.0

    hits = 0
    total = 0.0
    for idx, item_id in enumerate(ranked, start=1):
        if item_id not in relevant:
            continue
        hits += 1
        total += hits / idx

    return total / len(relevant)


def intra_list_category_diversity(categories: Sequence[str]) -> float:
    if not categories:
        return 0.0
    return len(set(categories)) / len(categories)
