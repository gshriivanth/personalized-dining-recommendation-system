# src/utils/__init__.py
"""
Utility functions for the nutrition recommendation system.

Provides helper functions for I/O operations and data processing.
"""

from src.utils.io import read_json, write_json

__all__ = ["read_json", "write_json"]
