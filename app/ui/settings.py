from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from analytics.date_ranges import DateRange
from db.repository import get_setting
from db.seed_demo import seed_from_demo_file
from exports.csv_export import export_rankings_csv
from exports.pdf_export import export_rankings_pdf
from spotify.auth import (
    OAUTH_STATE_SESSION_KEY,
    OAuthConfigError,
    build_authorize_url,
    disconnect_spotify,
    exchange_code_for_token,
    generate_state_token,
    get_token_info,
    is_connected,
)
from spotify.client import current_user_profile
from spotify.sync import LAST_SYNC_KEY, import_extended_history_files, sync_recently_played


def render_settings_page(date_range: DateRange) -> None:
    st.title("Settings")
    st.caption(f"Date range: {date_range.start.isoformat()} to {date_range.end.isoformat()}")

    connect_tab, import_tab, export_tab = st.tabs(["Connect", "Import", "Export"])

    with connect_tab:
        _render_connect_section()

    with import_tab:
        _render_import_section()

    with export_tab:
        _render_export_section(date_range)


def _render_connect_section() -> None:
    st.subheader("Spotify OAuth")

    try:
        _handle_oauth_callback()
    except OAuthConfigError as exc:
        st.error(str(exc))
        st.code("python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        return
    except Exception as exc:  # noqa: BLE001
        st.error(f"OAuth callback failed: {exc}")

    connected = is_connected()
    token_info = get_token_info() if connected else None

    if connected:
        st.success("Spotify connected.")
        profile = current_user_profile()
        if profile:
            st.write(f"Signed in as: **{profile.get('display_name') or profile.get('id', 'Spotify user')}**")
        if token_info:
            st.caption(f"Token expires at epoch: {token_info.get('expires_at')}")

        if st.button("Sync Recently Played", use_container_width=True, type="primary"):
            try:
                with st.spinner("Syncing recently played..."):
                    inserted = sync_recently_played(limit=50)
                st.success(f"Sync complete. Inserted {inserted} listens.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Sync failed: {exc}")

        last_sync = get_setting(LAST_SYNC_KEY)
        if last_sync:
            st.caption(f"Last sync (UTC): {last_sync}")

        if st.button("Disconnect Spotify", use_container_width=True):
            disconnect_spotify()
            st.rerun()
    else:
        st.info("No Spotify account connected yet.")
        if st.button("Prepare Spotify Login", type="primary", use_container_width=True):
            state = generate_state_token()
            st.session_state[OAUTH_STATE_SESSION_KEY] = state
            st.session_state["spotify_authorize_url"] = build_authorize_url(state)

        authorize_url = st.session_state.get("spotify_authorize_url")
        if authorize_url:
            st.link_button("Open Spotify Authorization", authorize_url, use_container_width=True)
            st.caption("After approving in Spotify, you will be redirected back to this app.")


def _render_import_section() -> None:
    st.subheader("Historical Import")
    st.caption("Upload Spotify Extended Streaming History JSON files (StreamingHistory*.json).")

    uploaded = st.file_uploader(
        "Upload one or more JSON files",
        type=["json"],
        accept_multiple_files=True,
    )

    if uploaded and st.button("Import Uploaded Files", use_container_width=True):
        temp_paths: list[str] = []
        try:
            for file in uploaded:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                    tmp.write(file.getbuffer())
                    temp_paths.append(tmp.name)
            try:
                with st.spinner("Importing history files..."):
                    inserted = import_extended_history_files(temp_paths)
                st.success(f"Import complete. Inserted {inserted} listens.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Import failed: {exc}")
        finally:
            for path in temp_paths:
                Path(path).unlink(missing_ok=True)

    st.divider()
    st.subheader("Demo Mode")
    if st.button("Load bundled demo dataset", use_container_width=True):
        inserted = seed_from_demo_file()
        st.success(f"Demo data loaded. Processed {inserted} rows.")


def _render_export_section(date_range: DateRange) -> None:
    st.subheader("Export filtered rankings")
    entity = st.selectbox("Entity", ["songs", "artists", "albums", "genres"])

    csv_data = export_rankings_csv(entity, date_range)
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"spotify_{entity}_{date_range.start}_{date_range.end}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    pdf_data = export_rankings_pdf(entity, date_range)
    st.download_button(
        label="Download PDF",
        data=pdf_data,
        file_name=f"spotify_{entity}_{date_range.start}_{date_range.end}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


def _handle_oauth_callback() -> None:
    params = st.query_params
    code = params.get("code")
    returned_state = params.get("state")
    error = params.get("error")

    if error:
        st.error(f"Spotify OAuth error: {error}")
        _clear_oauth_query_params()
        return

    if not code:
        return

    expected_state = st.session_state.get(OAUTH_STATE_SESSION_KEY)
    if expected_state and returned_state != expected_state:
        st.error("OAuth state mismatch. Retry connection.")
        _clear_oauth_query_params()
        return

    exchange_code_for_token(code=code, state=returned_state)
    _clear_oauth_query_params()
    st.success("Spotify OAuth connection successful.")


def _clear_oauth_query_params() -> None:
    for key in ("code", "state", "error"):
        if key in st.query_params:
            del st.query_params[key]
