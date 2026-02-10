from __future__ import annotations
from typing import Any, Dict, List, Optional
import time
import requests

from src.config import USDA_FDC_API_KEY, USDA_FDC_BASE_URL

#client interface doesn't do any error handling, leaves that up to the caller
class USDAFoodDataCentralClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_s: int = 20,
        rate_limit_per_hour: Optional[int] = 1000,
    ):
        #use api_key parameter to override environment variable for testing
        self.api_key = api_key or USDA_FDC_API_KEY
        self.timeout_s = timeout_s #max time in secs to wait for an API response
        self._min_interval_s: Optional[float] = None
        self._last_call_s: Optional[float] = None
        if rate_limit_per_hour and rate_limit_per_hour > 0:
            self._min_interval_s = 3600.0 / rate_limit_per_hour
        if not self.api_key:
            raise RuntimeError(
                "Missing USDA FDC API key. Set environment variable USDA_FDC_API_KEY."
            )

    def _throttle(self) -> None:
        if self._min_interval_s is None:
            return
        now = time.monotonic()
        if self._last_call_s is None:
            self._last_call_s = now
            return
        elapsed = now - self._last_call_s
        if elapsed < self._min_interval_s:
            time.sleep(self._min_interval_s - elapsed)
        self._last_call_s = time.monotonic()
        
    def fetch_food(self, fdc_id: int) -> Dict[str, Any]:
        """
        GET /food/{fdcId}
        Returns raw JSON including foodNutrients[] for a single food item.
        """
        self._throttle()
        url = f"{USDA_FDC_BASE_URL}/food/{fdc_id}"
        response = requests.get(
            url,
            params = {"api_key": self.api_key},
            timeout = self.timeout_s
        )
        response.raise_for_status()
        return response.json()
    
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
        self._throttle()
        url = f"{USDA_FDC_BASE_URL}/foods/search"
        payload = {
            "query": query,
            "pageSize": page_size,
        }
        if data_type:
            payload["dataType"] = data_type
        
        response = requests.post(
            url, 
            params = {"api_key": self.api_key}, 
            json = payload,
            timeout = self.timeout_s,
        )
        response.raise_for_status()
        return response.json()
    
    def fetch_multiple_foods(self, fdc_ids: List[int]) -> Dict[str, Any]:
        """
        POST /foods
        Does what fetch_food method does but for multiple foods. 
        More rate limit friendly than fetch_foods.
        """
        self._throttle()
        url = f"{USDA_FDC_BASE_URL}/foods"
        response = requests.post(
            url,
            params = {"api_key": self.api_key},
            json = {"fdcIds": fdc_ids},
            timeout = self.timeout_s
        )
        response.raise_for_status()
        return response.json()
