"""Tests for USDA FoodData Central client.

Run unit tests:
  pytest -q
Run integration tests (requires USDA_FDC_API_KEY in env):
  pytest -m integration
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import pytest
import requests

from src.config import USDA_FDC_BASE_URL
from src.ingest import usda_fdc_client
from src.ingest.usda_fdc_client import USDAFoodDataCentralClient

_CALL_TIMESTAMPS: list[float] = []


def _rate_limit_calls(max_per_hour: int = 1000) -> None:
    """Best-effort limiter for integration tests to respect API limits."""
    now = time.time()
    window_start = now - 3600
    while _CALL_TIMESTAMPS and _CALL_TIMESTAMPS[0] < window_start:
        _CALL_TIMESTAMPS.pop(0)
    if len(_CALL_TIMESTAMPS) >= max_per_hour:
        sleep_s = _CALL_TIMESTAMPS[0] - window_start
        if sleep_s > 0:
            time.sleep(sleep_s)
    _CALL_TIMESTAMPS.append(time.time())


class FakeResponse:
    def __init__(self, json_data: Any, raise_exc: Optional[Exception] = None):
        self._json_data = json_data
        self._raise_exc = raise_exc

    def raise_for_status(self) -> None:
        if self._raise_exc:
            raise self._raise_exc

    def json(self) -> Any:
        return self._json_data


def test_init_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(usda_fdc_client, "USDA_FDC_API_KEY", None)
    with pytest.raises(RuntimeError):
        USDAFoodDataCentralClient()


def test_init_with_api_key() -> None:
    client = USDAFoodDataCentralClient(api_key="TESTKEY", timeout_s=10)
    assert client.api_key == "TESTKEY"
    assert client.timeout_s == 10


def test_search_foods_posts_with_payload_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_post(url: str, params: Dict[str, Any], json: Dict[str, Any], timeout: int):
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse({"foods": []})

    monkeypatch.setattr(requests, "post", fake_post)
    client = USDAFoodDataCentralClient(api_key="TESTKEY", timeout_s=7)

    result = client.search_foods("apple", page_size=5, data_type=["Foundation"])

    assert captured["url"] == f"{USDA_FDC_BASE_URL}/foods/search"
    assert captured["params"] == {"api_key": "TESTKEY"}
    assert captured["json"] == {
        "query": "apple",
        "pageSize": 5,
        "dataType": ["Foundation"],
    }
    assert captured["timeout"] == 7
    assert result == {"foods": []}


def test_search_foods_propagates_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, params: Dict[str, Any], json: Dict[str, Any], timeout: int):
        return FakeResponse({}, raise_exc=requests.HTTPError("boom"))

    monkeypatch.setattr(requests, "post", fake_post)
    client = USDAFoodDataCentralClient(api_key="TESTKEY")

    with pytest.raises(requests.HTTPError):
        client.search_foods("apple")


def test_fetch_food_gets_with_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_get(url: str, params: Dict[str, Any], timeout: int):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse({"fdcId": 1})

    monkeypatch.setattr(requests, "get", fake_get)
    client = USDAFoodDataCentralClient(api_key="TESTKEY", timeout_s=9)

    result = client.fetch_food(123)

    assert captured["url"] == f"{USDA_FDC_BASE_URL}/food/123"
    assert captured["params"] == {"api_key": "TESTKEY"}
    assert captured["timeout"] == 9
    assert result == {"fdcId": 1}


def test_fetch_food_propagates_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: Dict[str, Any], timeout: int):
        return FakeResponse({}, raise_exc=requests.HTTPError("boom"))

    monkeypatch.setattr(requests, "get", fake_get)
    client = USDAFoodDataCentralClient(api_key="TESTKEY")

    with pytest.raises(requests.HTTPError):
        client.fetch_food(123)


def test_fetch_multiple_foods_posts_payload_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_post(url: str, params: Dict[str, Any], json: Dict[str, Any], timeout: int):
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse([{"fdcId": 1}, {"fdcId": 2}])

    monkeypatch.setattr(requests, "post", fake_post)
    client = USDAFoodDataCentralClient(api_key="TESTKEY", timeout_s=11)

    result = client.fetch_multiple_foods([1, 2])

    assert captured["url"] == f"{USDA_FDC_BASE_URL}/foods"
    assert captured["params"] == {"api_key": "TESTKEY"}
    assert captured["json"] == {"fdcIds": [1, 2]}
    assert captured["timeout"] == 11
    assert result == [{"fdcId": 1}, {"fdcId": 2}]


def test_fetch_multiple_foods_propagates_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, params: Dict[str, Any], json: Dict[str, Any], timeout: int):
        return FakeResponse({}, raise_exc=requests.HTTPError("boom"))

    monkeypatch.setattr(requests, "post", fake_post)
    client = USDAFoodDataCentralClient(api_key="TESTKEY")

    with pytest.raises(requests.HTTPError):
        client.fetch_multiple_foods([1, 2])


@pytest.mark.integration
def test_integration_search_and_fetch_food() -> None:
    api_key = os.getenv("USDA_FDC_API_KEY")
    if not api_key:
        pytest.skip("USDA_FDC_API_KEY not set")

    client = USDAFoodDataCentralClient(api_key=api_key)
    _rate_limit_calls()
    search_result = client.search_foods("oatmeal", page_size=1)

    foods = search_result.get("foods", [])
    assert foods, "Expected at least one food from search"

    fdc_id = foods[0].get("fdcId")
    assert fdc_id is not None, "Expected fdcId in search result"

    _rate_limit_calls()
    food_detail = client.fetch_food(int(fdc_id))
    assert "foodNutrients" in food_detail
