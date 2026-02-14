from __future__ import annotations


def classify_era(total_minutes: float, unique_artists: int, repeat_ratio: float) -> str:
    if total_minutes > 5000 and repeat_ratio > 0.7:
        return "Deep Replay Era"
    if unique_artists > 250 and repeat_ratio < 0.45:
        return "Discovery Era"
    if total_minutes > 2500:
        return "Heavy Rotation Era"
    return "Casual Listening Era"
