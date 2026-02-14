from __future__ import annotations

from analytics.metrics import safe_delta_pct


def render_insight_text(summary: dict[str, float], previous: dict[str, float]) -> list[str]:
    peak_hour = int(summary.get("peak_hour", 0))
    weekday_minutes = summary.get("weekday_minutes", 0.0)
    weekend_minutes = summary.get("weekend_minutes", 0.0)
    repeat_ratio = summary.get("repeat_ratio", 0.0)
    discovery_ratio = max(0.0, 1.0 - repeat_ratio)

    minutes_delta = safe_delta_pct(summary.get("minutes", 0.0), previous.get("minutes", 0.0))
    plays_delta = safe_delta_pct(summary.get("plays", 0.0), previous.get("plays", 0.0))

    day_bias = "weekdays" if weekday_minutes >= weekend_minutes else "weekends"

    return [
        f"Your peak listening hour is around {peak_hour:02d}:00.",
        f"You skew toward {day_bias} ({weekday_minutes:.1f} vs {weekend_minutes:.1f} minutes).",
        f"Discovery vs repeat is {discovery_ratio:.0%} new-like plays and {repeat_ratio:.0%} repeats.",
        f"Compared with the previous period, listening time changed by {minutes_delta:+.1f}% and plays by {plays_delta:+.1f}%.",
    ]
