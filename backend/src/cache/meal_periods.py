# src/cache/meal_periods.py
"""
UCI Dining Hall meal period schedule.

Defines the complete set of named meal periods for Brandywine and Anteatery,
including the day-of-week and time constraints for each.  The schedule mirrors
the actual UCI dining calendar as closely as possible; adjust the time windows
here if the dining halls change their hours.

Meal periods in order per weekday:
  Breakfast       Mon–Fri   07:00–10:30
  Lunch           Mon–Fri   11:00–14:30
  Afternoon Snack Mon–Fri   14:30–17:00
  Dinner          Mon–Sun   17:00–20:30
  Evening Snack   Mon–Thu   20:30–23:00

Weekend (Sat–Sun):
  Brunch          Sat–Sun   09:00–14:30   (replaces Breakfast + Lunch)
  Dinner          Mon–Sun   17:00–20:30   (same as weekdays)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional, Set


@dataclass(frozen=True)
class MealPeriodWindow:
    name: str
    days: frozenset  # 0=Monday … 6=Sunday
    start: time      # local wall-clock start (inclusive)
    end: time        # local wall-clock end   (exclusive)

    def is_active(self, dt: datetime) -> bool:
        return dt.weekday() in self.days and self.start <= dt.time() < self.end

    def ends_at(self, on_date: date) -> datetime:
        """Return the datetime when this period ends on the given date."""
        return datetime.combine(on_date, self.end)


# Ordered list — first match wins when checking the current period.
UCI_MEAL_PERIODS: list[MealPeriodWindow] = [
    MealPeriodWindow(
        name="breakfast",
        days=frozenset({0, 1, 2, 3, 4}),   # Mon–Fri
        start=time(7, 0),
        end=time(10, 30),
    ),
    MealPeriodWindow(
        name="brunch",
        days=frozenset({5, 6}),             # Sat–Sun
        start=time(9, 0),
        end=time(14, 30),
    ),
    MealPeriodWindow(
        name="lunch",
        days=frozenset({0, 1, 2, 3, 4}),   # Mon–Fri
        start=time(11, 0),
        end=time(14, 30),
    ),
    MealPeriodWindow(
        name="afternoon_snack",
        days=frozenset({0, 1, 2, 3, 4}),   # Mon–Fri
        start=time(14, 30),
        end=time(17, 0),
    ),
    MealPeriodWindow(
        name="dinner",
        days=frozenset({0, 1, 2, 3, 4, 5, 6}),  # Every day
        start=time(17, 0),
        end=time(20, 30),
    ),
    MealPeriodWindow(
        name="evening_snack",
        days=frozenset({0, 1, 2, 3}),       # Mon–Thu
        start=time(20, 30),
        end=time(23, 0),
    ),
]

# Which meal periods are considered "main" meals for top-level recommendation UI.
# Afternoon/Evening Snack are valid but shown differently in the app.
MAIN_MEAL_PERIODS = {"breakfast", "brunch", "lunch", "dinner"}


def get_current_period(now: Optional[datetime] = None) -> Optional[MealPeriodWindow]:
    """Return the active MealPeriodWindow for the given (or current) datetime."""
    dt = now or datetime.now()
    for period in UCI_MEAL_PERIODS:
        if period.is_active(dt):
            return period
    return None


def get_cache_key(hall: str, now: Optional[datetime] = None) -> Optional[str]:
    """
    Return a deterministic cache key for the current meal period at *hall*.
    Returns None when the dining hall is between meal periods (closed).

    Key format: ``{hall}:{YYYY-MM-DD}:{period_name}``
    Example:    ``brandywine:2026-03-07:lunch``
    """
    dt = now or datetime.now()
    period = get_current_period(dt)
    if period is None:
        return None
    return f"{hall}:{dt.date().isoformat()}:{period.name}"


def seconds_until_period_ends(now: Optional[datetime] = None) -> Optional[int]:
    """
    Return the number of seconds until the current meal period ends.
    Returns None when not inside any meal period.
    """
    dt = now or datetime.now()
    period = get_current_period(dt)
    if period is None:
        return None
    ends_at = period.ends_at(dt.date())
    return max(0, int((ends_at - dt).total_seconds()))


def is_hall_open(now: Optional[datetime] = None) -> bool:
    return get_current_period(now) is not None
