from datetime import date

from app.ui.date_filter import date_range_from_preset


def test_last_week_range() -> None:
    # Friday Jan 10, 2025 -> last week should be Dec 30, 2024 to Jan 5, 2025
    result = date_range_from_preset("last_week", today=date(2025, 1, 10))
    assert result.start == date(2024, 12, 30)
    assert result.end == date(2025, 1, 5)


def test_last_3_years_range() -> None:
    result = date_range_from_preset("last_3_years", today=date(2026, 2, 14))
    assert result.start == date(2024, 1, 1)
    assert result.end == date(2026, 2, 14)
