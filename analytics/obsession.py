from __future__ import annotations


def obsession_score(plays: int, total_ms: int, repeat_density: float, recency_days: int) -> float:
    plays_component = min(plays / 50.0, 1.0)
    time_component = min(total_ms / (1000 * 60 * 120), 1.0)
    repeat_component = min(max(repeat_density, 0.0), 1.0)
    recency_component = 1.0 / (1.0 + max(recency_days, 0) / 30.0)
    score = (
        plays_component * 0.35
        + time_component * 0.25
        + repeat_component * 0.20
        + recency_component * 0.20
    ) * 100.0
    return round(score, 2)
