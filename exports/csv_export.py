from __future__ import annotations

from analytics.date_ranges import DateRange
from db.repository import top_albums, top_artists, top_genres, top_songs


def export_rankings_csv(entity: str, date_range: DateRange) -> bytes:
    if entity == "songs":
        df = top_songs(date_range)
    elif entity == "artists":
        df = top_artists(date_range)
    elif entity == "albums":
        df = top_albums(date_range)
    elif entity == "genres":
        df = top_genres(date_range)
    else:
        raise ValueError(f"Unsupported entity for CSV export: {entity}")
    return df.to_csv(index=False).encode("utf-8")
