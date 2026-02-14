from analytics.diversity import diversity_score


def test_diversity_score_bounds() -> None:
    result = diversity_score([100, 100, 100], [50, 30, 20])
    assert 0 <= result["score"] <= 100
    assert result["genre_component"] > 0
    assert result["artist_component"] > 0
