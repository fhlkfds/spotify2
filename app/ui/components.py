from __future__ import annotations

import streamlit as st


def metric_row(values: list[tuple[str, str, str | None]]) -> None:
    cols = st.columns(len(values))
    for col, (label, value, delta) in zip(cols, values, strict=False):
        with col:
            st.metric(label=label, value=value, delta=delta)


def empty_state(message: str) -> None:
    st.info(message)
