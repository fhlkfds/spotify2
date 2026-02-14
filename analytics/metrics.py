from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta


def consecutive_streak(days_with_listens: Iterable[date]) -> int:
    days = sorted(set(days_with_listens))
    if not days:
        return 0
    longest = 1
    current = 1
    for idx in range(1, len(days)):
        if (days[idx] - days[idx - 1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def current_streak_to_today(days_with_listens: Iterable[date], today: date | None = None) -> int:
    today = today or date.today()
    day_set = set(days_with_listens)
    streak = 0
    cursor = today
    while cursor in day_set:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def safe_delta_pct(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100.0
