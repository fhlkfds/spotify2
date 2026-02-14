from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date
    label: str = "Custom"


def to_datetime_bounds(date_range: DateRange) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(date_range.start, time.min)
    end_dt = datetime.combine(date_range.end + timedelta(days=1), time.min)
    return start_dt, end_dt


def previous_period(date_range: DateRange) -> DateRange:
    length_days = (date_range.end - date_range.start).days + 1
    prev_end = date_range.start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length_days - 1)
    return DateRange(start=prev_start, end=prev_end, label="Previous Period")


def bucket_for_range(date_range: DateRange) -> str:
    days = (date_range.end - date_range.start).days + 1
    if days <= 31:
        return "day"
    if days <= 365:
        return "week"
    return "month"
