import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

#building a general project root to be used any device with this repository stored locally
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

#loads api key from locally stored environment variables
USDA_FDC_API_KEY_ENV = "USDA_FDC_API_KEY"
USDA_FDC_API_KEY = os.getenv(USDA_FDC_API_KEY_ENV)

DATABASE_URL_ENV = "DATABASE_URL"
DATABASE_URL = os.getenv(DATABASE_URL_ENV)

USDA_FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

USDA_FDC_SEARCH_RAW_CACHE = CACHE_DIR / "usda_fdc_search_raw.json"
USDA_FDC_DETAILS_RAW_CACHE = CACHE_DIR / "usda_fdc_details_raw.json"
USDA_FDC_DOCS_CACHE = CACHE_DIR / "usda_fdc_docs.json"
