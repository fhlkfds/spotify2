from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.types import DateRange


@dataclass(frozen=True)
class Preset:
    key: str
    label: str


PRESETS: tuple[Preset, ...] = (
    Preset("today", "Today"),
    Preset("yesterday", "Yesterday"),
    Preset("this_week", "This Week"),
    Preset("last_week", "Last Week"),
    Preset("this_month", "This Month"),
    Preset("last_month", "Last Month"),
    Preset("this_year", "This Year"),
    Preset("last_year", "Last Year"),
    Preset("last_3_years", "Last 3 Years"),
    Preset("custom", "Custom"),
)

DEFAULT_PRESET_KEY = "this_month"


def _start_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _end_of_week(day: date) -> date:
    return _start_of_week(day) + timedelta(days=6)


def _start_of_month(day: date) -> date:
    return day.replace(day=1)


def _end_of_month(day: date) -> date:
    if day.month == 12:
        next_month = day.replace(year=day.year + 1, month=1, day=1)
    else:
        next_month = day.replace(month=day.month + 1, day=1)
    return next_month - timedelta(days=1)


def date_range_from_preset(key: str, today: date | None = None) -> DateRange:
    current = today or date.today()
    if key == "today":
        return DateRange(start=current, end=current, label="Today")
    if key == "yesterday":
        day = current - timedelta(days=1)
        return DateRange(start=day, end=day, label="Yesterday")
    if key == "this_week":
        return DateRange(start=_start_of_week(current), end=current, label="This Week")
    if key == "last_week":
        start_this = _start_of_week(current)
        end_last = start_this - timedelta(days=1)
        start_last = _start_of_week(end_last)
        return DateRange(start=start_last, end=_end_of_week(start_last), label="Last Week")
    if key == "this_month":
        return DateRange(start=_start_of_month(current), end=current, label="This Month")
    if key == "last_month":
        end_last = _start_of_month(current) - timedelta(days=1)
        start_last = _start_of_month(end_last)
        return DateRange(start=start_last, end=_end_of_month(start_last), label="Last Month")
    if key == "this_year":
        start = date(current.year, 1, 1)
        return DateRange(start=start, end=current, label="This Year")
    if key == "last_year":
        start = date(current.year - 1, 1, 1)
        end = date(current.year - 1, 12, 31)
        return DateRange(start=start, end=end, label="Last Year")
    if key == "last_3_years":
        start = date(current.year - 2, 1, 1)
        return DateRange(start=start, end=current, label="Last 3 Years")
    return DateRange(start=current, end=current, label="Custom")


def preset_options() -> list[str]:
    return [preset.label for preset in PRESETS]


def preset_key_by_label(label: str) -> str:
    for preset in PRESETS:
        if preset.label == label:
            return preset.key
    return DEFAULT_PRESET_KEY


def preset_label_by_key(key: str) -> str:
    for preset in PRESETS:
        if preset.key == key:
            return preset.label
    return "This Month"
