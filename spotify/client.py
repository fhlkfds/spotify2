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


def artist_image_urls(artists: list[tuple[str, str]]) -> dict[str, str]:
    valid_ids = [artist_id for artist_id, _ in artists if artist_id and not artist_id.startswith("art_")]

    try:
        client = get_spotify_client()
    except RuntimeError:
        return {}

    image_by_artist: dict[str, str] = {}
    for i in range(0, len(valid_ids), 50):
        batch = valid_ids[i : i + 50]
        try:
            payload = client.artists(batch)
        except SpotifyException:
            continue
        for artist in payload.get("artists", []):
            artist_id = artist.get("id")
            images = artist.get("images") or []
            if artist_id and images:
                image_by_artist[artist_id] = images[0].get("url", "")

    for artist_id, artist_name in artists:
        if not artist_name or artist_id in image_by_artist:
            continue
        try:
            result = client.search(q=f"artist:{artist_name}", type="artist", limit=1)
            items = result.get("artists", {}).get("items", [])
            if not items:
                continue
            images = items[0].get("images") or []
            if images:
                image_by_artist[artist_id] = images[0].get("url", "")
        except SpotifyException:
            continue

    return {k: v for k, v in image_by_artist.items() if v}
