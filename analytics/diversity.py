from __future__ import annotations

import math


def _normalized_entropy(values: list[float]) -> float:
    cleaned = [v for v in values if v > 0]
    total = sum(cleaned)
    if total <= 0 or len(cleaned) <= 1:
        return 0.0
    probs = [v / total for v in cleaned]
    entropy = -sum(p * math.log(p) for p in probs)
    max_entropy = math.log(len(probs))
    if max_entropy == 0:
        return 0.0
    return entropy / max_entropy


def diversity_score(genre_minutes: list[float], artist_minutes: list[float]) -> dict[str, float]:
    genre_component = _normalized_entropy(genre_minutes)
    artist_component = _normalized_entropy(artist_minutes)
    score = (genre_component * 0.55 + artist_component * 0.45) * 100.0
    return {
        "score": round(score, 2),
        "genre_component": round(genre_component * 100.0, 2),
        "artist_component": round(artist_component * 100.0, 2),
    }
