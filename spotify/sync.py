from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

from db.repository import refresh_daily_aggregate_for_day, set_setting
from db.session import SessionLocal
from spotify.client import get_spotify_client
from spotify.metadata_resolver import search_track_id

LAST_SYNC_KEY = "spotify_last_sync_utc"
MS_TOLERANCE = 1000


def _synthetic_track_id(track_name: str, artist_name: str, album_name: str) -> str:
    value = f"{track_name}|{artist_name}|{album_name}"
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return f"local_{digest[:20]}"


def _dedupe_exists(session: Any, played_at: datetime, track_id: str, ms_played: int) -> bool:
    row = session.execute(
        text(
            """
            SELECT 1
            FROM listens
            WHERE played_at = :played_at
              AND track_id = :track_id
              AND ms_played BETWEEN :ms_min AND :ms_max
            LIMIT 1
            """
        ),
        {
            "played_at": played_at,
            "track_id": track_id,
            "ms_min": max(0, ms_played - MS_TOLERANCE),
            "ms_max": ms_played + MS_TOLERANCE,
        },
    ).first()
    return row is not None


def _upsert_track_bundle(
    session: Any,
    *,
    track_id: str,
    track_name: str,
    album_id: str,
    album_name: str,
    duration_ms: int | None,
    explicit: bool | None,
    popularity: int | None,
    artist_ids: list[str],
    artist_names: list[str],
) -> None:
    session.execute(
        text(
            """
            INSERT INTO albums(id, name)
            VALUES(:id, :name)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name
            """
        ),
        {"id": album_id, "name": album_name},
    )

    session.execute(
        text(
            """
            INSERT INTO tracks(id, name, album_id, duration_ms, explicit, popularity)
            VALUES(:id, :name, :album_id, :duration_ms, :explicit, :popularity)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                album_id=excluded.album_id,
                duration_ms=excluded.duration_ms,
                explicit=excluded.explicit,
                popularity=excluded.popularity
            """
        ),
        {
            "id": track_id,
            "name": track_name,
            "album_id": album_id,
            "duration_ms": duration_ms,
            "explicit": explicit,
            "popularity": popularity,
        },
    )

    for artist_id, artist_name in zip(artist_ids, artist_names, strict=False):
        session.execute(
            text(
                """
                INSERT INTO artists(id, name)
                VALUES(:id, :name)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name
                """
            ),
            {"id": artist_id, "name": artist_name},
        )
        session.execute(
            text(
                """
                INSERT OR IGNORE INTO track_artists(track_id, artist_id)
                VALUES(:track_id, :artist_id)
                """
            ),
            {"track_id": track_id, "artist_id": artist_id},
        )


def sync_recently_played(limit: int = 50) -> int:
    client = get_spotify_client()
    payload = client.current_user_recently_played(limit=limit)
    items: list[dict[str, Any]] = payload.get("items", [])

    inserted = 0
    touched_days: set[datetime.date] = set()

    with SessionLocal() as session:
        for item in items:
            track = item.get("track") or {}
            played_at_raw = item.get("played_at")
            if not played_at_raw:
                continue

            played_at = datetime.fromisoformat(played_at_raw.replace("Z", "+00:00")).astimezone(UTC)
            track_id = track.get("id")
            if not track_id:
                continue
            ms_played = int(track.get("duration_ms") or 0)

            album = track.get("album") or {}
            album_id = album.get("id") or f"alb_{track_id}"
            album_name = album.get("name") or "Unknown Album"

            artists = track.get("artists") or []
            artist_ids = [a.get("id") or f"art_{idx}_{track_id}" for idx, a in enumerate(artists)]
            artist_names = [a.get("name") or "Unknown Artist" for a in artists]

            _upsert_track_bundle(
                session,
                track_id=track_id,
                track_name=track.get("name") or "Unknown Track",
                album_id=album_id,
                album_name=album_name,
                duration_ms=track.get("duration_ms"),
                explicit=track.get("explicit"),
                popularity=track.get("popularity"),
                artist_ids=artist_ids,
                artist_names=artist_names,
            )

            if _dedupe_exists(session, played_at, track_id, ms_played):
                continue

            context = item.get("context") or {}
            session.execute(
                text(
                    """
                    INSERT INTO listens(played_at, ms_played, track_id, context_type, context_id, device_name)
                    VALUES(:played_at, :ms_played, :track_id, :context_type, :context_id, :device_name)
                    """
                ),
                {
                    "played_at": played_at,
                    "ms_played": ms_played,
                    "track_id": track_id,
                    "context_type": context.get("type"),
                    "context_id": context.get("uri"),
                    "device_name": None,
                },
            )
            touched_days.add(played_at.date())
            inserted += 1

        session.commit()

    for day in touched_days:
        refresh_daily_aggregate_for_day(day)

    set_setting(LAST_SYNC_KEY, datetime.now(UTC).isoformat())
    return inserted


def import_extended_history_file(path: str) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return 0

    inserted = 0
    touched_days: set[datetime.date] = set()

    with SessionLocal() as session:
        for item in data:
            ts = item.get("ts")
            if not ts:
                continue
            played_at = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(UTC)
            track_name = item.get("master_metadata_track_name") or "Unknown Track"
            artist_name = item.get("master_metadata_album_artist_name") or "Unknown Artist"
            album_name = item.get("master_metadata_album_album_name") or "Unknown Album"
            uri = item.get("spotify_track_uri")
            track_id = uri.split(":")[-1] if uri else None
            if not track_id:
                resolved = search_track_id(track_name, artist_name)
                track_id = resolved or _synthetic_track_id(track_name, artist_name, album_name)

            album_id = f"alb_{hashlib.sha1(album_name.encode('utf-8')).hexdigest()[:16]}"
            artist_id = f"art_{hashlib.sha1(artist_name.encode('utf-8')).hexdigest()[:16]}"
            ms_played = int(item.get("ms_played") or 0)

            _upsert_track_bundle(
                session,
                track_id=track_id,
                track_name=track_name,
                album_id=album_id,
                album_name=album_name,
                duration_ms=None,
                explicit=None,
                popularity=None,
                artist_ids=[artist_id],
                artist_names=[artist_name],
            )

            if _dedupe_exists(session, played_at, track_id, ms_played):
                continue

            session.execute(
                text(
                    """
                    INSERT INTO listens(played_at, ms_played, track_id, context_type, context_id, device_name)
                    VALUES(:played_at, :ms_played, :track_id, :context_type, :context_id, :device_name)
                    """
                ),
                {
                    "played_at": played_at,
                    "ms_played": ms_played,
                    "track_id": track_id,
                    "context_type": None,
                    "context_id": None,
                    "device_name": None,
                },
            )
            touched_days.add(played_at.date())
            inserted += 1

        session.commit()

    for day in touched_days:
        refresh_daily_aggregate_for_day(day)

    return inserted


def import_extended_history_files(paths: list[str]) -> int:
    total = 0
    for path in paths:
        total += import_extended_history_file(path)
    return total
