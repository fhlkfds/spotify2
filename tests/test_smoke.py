from app.ui.date_filter import date_range_from_preset


def test_preset_today_label() -> None:
    result = date_range_from_preset("today")
    assert result.label == "Today"
