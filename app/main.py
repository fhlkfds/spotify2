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


st.set_page_config(page_title="Spotify Stats", page_icon="🎧", layout="wide")
load_dotenv()
init_state(st.session_state)

with st.sidebar:
    st.header("Spotify Stats")
    st.caption("Reference-style navigation and global filters")

    grouped_pages: dict[str, list] = defaultdict(list)
    for page in PAGES:
        grouped_pages[page.group].append(page)

    for group, pages in grouped_pages.items():
        st.markdown(f"**{group}**")
        for page in pages:
            if st.button(page.label, use_container_width=True, key=f"nav_{page.key}"):
                st.session_state[PAGE_STATE_KEY] = page.key

    st.divider()
    st.markdown("**Global date filter**")
    quick_presets = [p for p in PRESETS if p.key != "custom"]
    quick_cols = st.columns(3)
    for idx, preset in enumerate(quick_presets):
        with quick_cols[idx % 3]:
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
