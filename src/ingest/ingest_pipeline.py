from __future__ import annotations
from typing import Dict, List, Any, Optional
import re

from src.types import Document
from src.utils.io import read_json, write_json
from src.config import USDA_FDC_DETAILS_RAW_CACHE, USDA_FDC_SEARCH_RAW_CACHE, USDA_FDC_DOCS_CACHE

from src.ingest.usda_fdc_client import USDAFoodDataCentralClient


