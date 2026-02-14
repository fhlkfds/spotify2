from datetime import date

from analytics.metrics import consecutive_streak, current_streak_to_today


def test_consecutive_streak_longest_segment() -> None:
    days = [
        date(2026, 2, 1),
        date(2026, 2, 2),
        date(2026, 2, 5),
        date(2026, 2, 6),
        date(2026, 2, 7),
    ]
    assert consecutive_streak(days) == 3


def test_current_streak_to_today() -> None:
    today = date(2026, 2, 14)
    days = [date(2026, 2, 12), date(2026, 2, 13), date(2026, 2, 14)]
    assert current_streak_to_today(days, today=today) == 3
