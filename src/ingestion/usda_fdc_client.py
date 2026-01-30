from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests

from src.config import USDA_FDC_API_KEY, USDA_FDC_BASE_URL

class USDAFoodDataCentralClient:
    def __init__(self, api_key: Optional[str] = None, timeout_s: int = 20):
        #use api_key parameter to override environment variable for testing
        self.api_key = api_key or USDA_FDC_API_KEY
        self.timeout_s = timeout_s #max time in secs to wait for an API response
        if not self.api_key:
            raise RuntimeError(
                "Missing USDA FDC API key. Set environment variable USDA_FDC_API_KEY."
            )
        
    def search_foods(
        self,
        query: str,
        page_size: int = 25,
        data_type: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        POST /foods/search
        Returns raw JSON containing foods[] with fdcId, description, dataType, etc.
        """
        url = f"{USDA_FDC_BASE_URL}/foods/search"
        payload = {
            "query": query,
            "pageSize": page_size,
        }
        if data_type:
            payload["dataType"] = data_type
        
        response = requests.post(
            url,
            params = {"api_key": self.api_key}
            json = payload
            timeout = self.timeout_s,
        )
        response.raise_for_status()
        return response.json()
