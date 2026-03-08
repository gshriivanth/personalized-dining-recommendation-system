# src/cache/dining_cache.py
"""
In-memory TTL cache for UCI dining hall menus.

Architecture
------------
The cache is a module-level singleton dict:

  _store: { cache_key -> (List[Food], expires_at: datetime) }

The cache key encodes the hall, date, and meal period (see meal_periods.get_cache_key).
An entry is valid only while the current wall-clock time is before expires_at, which
is set to the end of the meal period at the time of population.  Because the key
changes every time a new meal period starts, stale entries are never served — even
without explicit eviction — but we still prune them to prevent unbounded growth.

Plugging in Redis
-----------------
If you later want to replace this with Redis (e.g. when running multiple API
workers), swap the two helper functions `_cache_get` / `_cache_set` to use a
`redis.Redis` client.  The rest of the module stays the same.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.cache.meal_periods import get_cache_key, seconds_until_period_ends
from src.logical_view.food import Food

logger = logging.getLogger(__name__)

# { key: (serialized_foods_json, expires_at) }
_store: Dict[str, Tuple[str, datetime]] = {}
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Low-level get / set — swap these two functions for Redis
# ---------------------------------------------------------------------------

def _cache_get(key: str) -> Optional[str]:
    """Return the cached JSON string if the key exists and has not expired."""
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        payload, expires_at = entry
        if datetime.now() >= expires_at:
            del _store[key]
            return None
        return payload


def _cache_set(key: str, payload: str, expires_at: datetime) -> None:
    """Store a payload with an absolute expiry timestamp."""
    with _lock:
        _store[key] = (payload, expires_at)
        _prune()


def _prune() -> None:
    """Remove all expired entries (called under the lock)."""
    now = datetime.now()
    expired = [k for k, (_, exp) in _store.items() if now >= exp]
    for k in expired:
        del _store[k]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def _serialize(foods: List[Food]) -> str:
    return json.dumps([f.to_dict() for f in foods])


def _deserialize(payload: str) -> List[Food]:
    return [Food.from_dict(d) for d in json.loads(payload)]


def get_cached_menu(hall: str, now: Optional[datetime] = None) -> Optional[List[Food]]:
    """
    Return the cached menu for *hall* during the current meal period, or None
    if the cache is cold (miss) or the hall is between meal periods.
    """
    key = get_cache_key(hall, now)
    if key is None:
        return None  # between periods — nothing to cache
    payload = _cache_get(key)
    if payload is None:
        return None
    logger.debug("Dining cache HIT: %s", key)
    return _deserialize(payload)


def set_cached_menu(hall: str, foods: List[Food], now: Optional[datetime] = None) -> None:
    """
    Store *foods* for *hall* in the cache.  The entry expires automatically at
    the end of the current meal period.
    """
    dt = now or datetime.now()
    key = get_cache_key(hall, dt)
    if key is None:
        logger.debug("Dining cache: not inside a meal period — skipping cache set for %s", hall)
        return

    ttl = seconds_until_period_ends(dt)
    if not ttl:
        return

    from datetime import timedelta
    expires_at = dt + timedelta(seconds=ttl)
    _cache_set(key, _serialize(foods), expires_at)
    logger.info("Dining cache SET: %s (TTL %ds, expires %s)", key, ttl, expires_at.strftime("%H:%M:%S"))


def invalidate(hall: str) -> None:
    """Force-expire the current cached menu for *hall* (useful for testing)."""
    key = get_cache_key(hall)
    if key:
        with _lock:
            _store.pop(key, None)
