from __future__ import annotations

from typing import Any

import spotipy
from spotipy.exceptions import SpotifyException

from spotify.auth import get_spotify_oauth, get_valid_token_info


def get_spotify_client() -> spotipy.Spotify:
    token_info = get_valid_token_info()
    if not token_info:
        raise RuntimeError("Spotify is not connected. Use Settings -> Connect first.")

    oauth = get_spotify_oauth()
    return spotipy.Spotify(
        auth_manager=oauth,
        requests_timeout=10,
        retries=3,
        status_retries=3,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
    )


def current_user_profile() -> dict[str, Any] | None:
    try:
        client = get_spotify_client()
        return client.current_user()
    except (SpotifyException, RuntimeError):
        return None


def current_playing() -> dict[str, Any] | None:
    try:
        client = get_spotify_client()
        return client.current_user_playing_track()
    except (SpotifyException, RuntimeError):
        return None
