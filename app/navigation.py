from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavPage:
    group: str
    key: str
    label: str


PAGES: tuple[NavPage, ...] = (
    NavPage("Core", "dashboard", "Dashboard"),
    NavPage("Core", "insights", "Insights"),
    NavPage("Core", "obsessed", "Obsessed"),
    NavPage("Library", "playlists", "Playlists"),
    NavPage("Library", "artists", "Artists"),
    NavPage("Library", "songs", "Songs"),
    NavPage("Library", "albums", "Albums"),
    NavPage("Library", "genres", "Genres"),
    NavPage("Analytics", "diversity", "Listening Diversity Score"),
    NavPage("Analytics", "genre_evolution", "Genre Evolution"),
    NavPage("Highlights", "wrapped", "Wrapped Clone"),
    NavPage("System", "settings", "Settings"),
)
