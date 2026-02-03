# src/ingest/__init__.py
"""
Data ingestion module for the nutrition recommendation system.

Provides interfaces for fetching food data from multiple sources:
- USDA FoodData Central API
- UCI dining hall menus (web scraping)

Combines data sources into a unified food database.
"""

from src.ingest.usda_fdc_client import USDAFoodDataCentralClient
from src.ingest.dininghall_sources import UCIDiningScraper, DiningMenuItem
from src.ingest.ingest_pipeline import (
    DataIngestionPipeline,
    parse_usda_food,
    infer_meal_category,
    infer_dietary_tags
)

__all__ = [
    "USDAFoodDataCentralClient",
    "UCIDiningScraper",
    "DiningMenuItem",
    "DataIngestionPipeline",
    "parse_usda_food",
    "infer_meal_category",
    "infer_dietary_tags"
]
