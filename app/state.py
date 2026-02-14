from __future__ import annotations

from app.navigation import PAGES
from app.types import DateRange
from app.ui.date_filter import DEFAULT_PRESET_KEY, date_range_from_preset

PAGE_STATE_KEY = "current_page"
DATE_RANGE_STATE_KEY = "date_range"
DATE_PRESET_STATE_KEY = "date_preset"


def init_state(session_state: dict) -> None:
    if PAGE_STATE_KEY not in session_state:
        session_state[PAGE_STATE_KEY] = PAGES[0].key
    if DATE_PRESET_STATE_KEY not in session_state:
        session_state[DATE_PRESET_STATE_KEY] = DEFAULT_PRESET_KEY
    if DATE_RANGE_STATE_KEY not in session_state:
        session_state[DATE_RANGE_STATE_KEY] = date_range_from_preset(DEFAULT_PRESET_KEY)


def get_date_range(session_state: dict) -> DateRange:
    return session_state[DATE_RANGE_STATE_KEY]
