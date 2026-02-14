from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from db.repository import refresh_daily_aggregate_for_day
from db.session import SessionLocal


def seed_from_demo_file(path: str = "data/demo_streaming_history.json") -> int:
    source = Path(path)
    if not source.exists():
        return 0

    items = json.loads(source.read_text(encoding="utf-8"))
    inserted = 0

    with SessionLocal() as session:
        for item in items:
            uri = item.get("spotify_track_uri") or "spotify:track:demo_unknown"
            track_id = uri.split(":")[-1]
            track_name = item.get("master_metadata_track_name") or "Unknown Track"
            artist_name = item.get("master_metadata_album_artist_name") or "Unknown Artist"
            album_name = item.get("master_metadata_album_album_name") or "Unknown Album"

            session.execute(
                text("INSERT OR IGNORE INTO albums(id, name) VALUES(:id, :name)"),
                {"id": f"alb_{album_name}".replace(" ", "_"), "name": album_name},
            )
            session.execute(
                text("INSERT OR IGNORE INTO artists(id, name) VALUES(:id, :name)"),
                {"id": f"art_{artist_name}".replace(" ", "_"), "name": artist_name},
            )
            session.execute(
                text("INSERT OR IGNORE INTO tracks(id, name, album_id) VALUES(:id, :name, :album_id)"),
                {
                    "id": track_id,
                    "name": track_name,
                    "album_id": f"alb_{album_name}".replace(" ", "_"),
                },
            )
            session.execute(
                text("INSERT OR IGNORE INTO track_artists(track_id, artist_id) VALUES(:track_id, :artist_id)"),
                {"track_id": track_id, "artist_id": f"art_{artist_name}".replace(" ", "_")},
            )
            played_at = datetime.fromisoformat(item["ts"].replace("Z", "+00:00")).astimezone(UTC)
            session.execute(
                text(
                    """
                INSERT OR IGNORE INTO listens(played_at, ms_played, track_id, context_type, context_id, device_name)
                VALUES(:played_at, :ms_played, :track_id, :context_type, :context_id, :device_name)
                """
                ),
                {
                    "played_at": played_at,
                    "ms_played": int(item.get("ms_played", 0)),
                    "track_id": track_id,
                    "context_type": None,
                    "context_id": None,
                    "device_name": None,
                },
            )
            inserted += 1
        session.commit()

    for item in items:
        day = datetime.fromisoformat(item["ts"].replace("Z", "+00:00")).date()
        refresh_daily_aggregate_for_day(day)

    return inserted
