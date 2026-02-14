from __future__ import annotations

from typing import Any

from spotipy.exceptions import SpotifyException

from spotify.client import get_spotify_client


def search_track_id(track_name: str, artist_name: str, client: Any | None = None) -> str | None:
    query = f"track:{track_name} artist:{artist_name}"
    try:
        spotify_client = client or get_spotify_client()
        result = spotify_client.search(q=query, type="track", limit=1)
    except (SpotifyException, RuntimeError):
        return None

    items: list[dict[str, Any]] = result.get("tracks", {}).get("items", [])
    if not items:
        return None
    return items[0].get("id")
