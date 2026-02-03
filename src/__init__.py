# src/__init__.py
"""
Personalized Dining Recommendation System

A nutrition-focused food recommendation system implementing traditional IR
techniques (inverted index, TF-IDF, BM25) with nutrition-aware ranking.

Modules:
- logical_view: Core data models (Food, UserGoals, ConsumedToday)
- ingest: Data ingestion from USDA FDC API and UCI dining halls
- index: Inverted index and nutrient vector index
- query: Food search and nutrition-specific ranking
- ranking: Traditional IR ranking algorithms (TF-IDF, BM25)
- utils: Utility functions
"""
from typing import List

__version__ = "0.1.0"
__all__: List[str] = []
