from __future__ import annotations

from collections import defaultdict

import streamlit as st
from dotenv import load_dotenv

from app.navigation import PAGES
from app.state import DATE_PRESET_STATE_KEY, DATE_RANGE_STATE_KEY, PAGE_STATE_KEY, init_state
from app.types import DateRange
from app.ui.date_filter import (
    PRESETS,
    date_range_from_preset,
    preset_key_by_label,
    preset_label_by_key,
    preset_options,
)
from app.ui.pages import render_page
from app.ui.theme import apply_theme


st.set_page_config(page_title="Spotify Stats", page_icon="🎧", layout="wide")
load_dotenv()
init_state(st.session_state)
apply_theme()

with st.sidebar:
    st.markdown(
        """
        <div class="brand-block">
          <div class="brand-kicker">Listening Analytics</div>
          <div class="brand-title">Spotify Stats</div>
          <div class="brand-sub">Global filters and dashboards</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page_by_key = {page.key: page for page in PAGES}
    page_keys = [page.key for page in PAGES]
    current_page = st.session_state.get(PAGE_STATE_KEY, page_keys[0])
    if current_page not in page_by_key:
        current_page = page_keys[0]
    st.session_state[PAGE_STATE_KEY] = current_page

    grouped_pages: dict[str, list] = defaultdict(list)
    for page in PAGES:
        grouped_pages[page.group].append(page)

    group_order = ["Core", "Library", "Analytics", "Highlights", "System"]
    current_group = page_by_key[current_page].group

    st.markdown("**Navigate**")
    for group in group_order:
        pages = grouped_pages.get(group, [])
        if not pages:
            continue
        with st.expander(group, expanded=group == current_group):
            for page in pages:
                is_active = page.key == st.session_state[PAGE_STATE_KEY]
                if st.button(
                    page.label,
                    key=f"nav_{page.key}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state[PAGE_STATE_KEY] = page.key

    st.divider()
    st.markdown("**Date range**")
    quick_presets = [p for p in PRESETS if p.key != "custom"]
    quick_cols = st.columns(2)
    for idx, preset in enumerate(quick_presets):
        with quick_cols[idx % 2]:
            if st.button(preset.label, key=f"preset_{preset.key}", use_container_width=True):
                st.session_state[DATE_PRESET_STATE_KEY] = preset.key
                st.session_state[DATE_RANGE_STATE_KEY] = date_range_from_preset(preset.key)

    selected_label = st.selectbox(
        "Preset",
        options=preset_options(),
        index=preset_options().index(preset_label_by_key(st.session_state[DATE_PRESET_STATE_KEY])),
        key="date_preset_label",
    )
    selected_key = preset_key_by_label(selected_label)

    if selected_key != "custom":
        st.session_state[DATE_PRESET_STATE_KEY] = selected_key
        st.session_state[DATE_RANGE_STATE_KEY] = date_range_from_preset(selected_key)
    else:
        current = st.session_state[DATE_RANGE_STATE_KEY]
        start = st.date_input("Start", value=current.start)
        end = st.date_input("End", value=current.end)
        if start <= end:
            st.session_state[DATE_PRESET_STATE_KEY] = "custom"
            st.session_state[DATE_RANGE_STATE_KEY] = DateRange(start=start, end=end, label="Custom")
        else:
            st.error("Start date must be before end date.")

render_page(st.session_state[PAGE_STATE_KEY], st.session_state[DATE_RANGE_STATE_KEY])
