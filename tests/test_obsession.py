from analytics.obsession import obsession_score


def test_obsession_score_increases_with_plays() -> None:
    low = obsession_score(plays=3, total_ms=200000, repeat_density=0.2, recency_days=40)
    high = obsession_score(plays=30, total_ms=200000, repeat_density=0.2, recency_days=40)
    assert high > low


def test_obsession_score_bounds() -> None:
    score = obsession_score(plays=999, total_ms=99999999, repeat_density=1.0, recency_days=0)
    assert 0 <= score <= 100
