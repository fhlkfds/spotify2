from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import text

from analytics.date_ranges import DateRange, to_datetime_bounds
from db.session import SessionLocal


@dataclass(frozen=True)
class Pagination:
    limit: int = 50
    offset: int = 0


def _fetch_df(sql: str, params: dict[str, Any]) -> pd.DataFrame:
    with SessionLocal() as session:
        conn = session.connection()
        return pd.read_sql_query(text(sql), conn, params=params)


def _range_params(date_range: DateRange) -> dict[str, Any]:
    start_dt, end_dt = to_datetime_bounds(date_range)
    return {"start": start_dt, "end": end_dt}


def get_kpis(date_range: DateRange) -> dict[str, float]:
    params = _range_params(date_range)
    df = _fetch_df(
        """
        SELECT
          COALESCE(SUM(l.ms_played), 0) / 60000.0 AS total_minutes,
          COUNT(*) AS plays,
          COUNT(DISTINCT t.id) AS unique_songs,
          COUNT(DISTINCT a.id) AS unique_artists,
          COUNT(DISTINCT al.id) AS unique_albums
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        LEFT JOIN track_artists ta ON ta.track_id = t.id
        LEFT JOIN artists a ON a.id = ta.artist_id
        LEFT JOIN albums al ON al.id = t.album_id
        WHERE l.played_at >= :start AND l.played_at < :end
        """,
        params,
    )
    if df.empty:
        return {"total_minutes": 0.0, "plays": 0, "unique_songs": 0, "unique_artists": 0, "unique_albums": 0}
    row = df.iloc[0]
    return {
        "total_minutes": float(row["total_minutes"] or 0.0),
        "plays": int(row["plays"] or 0),
        "unique_songs": int(row["unique_songs"] or 0),
        "unique_artists": int(row["unique_artists"] or 0),
        "unique_albums": int(row["unique_albums"] or 0),
    }


def listened_days(date_range: DateRange) -> list[date]:
    df = _fetch_df(
        """
        SELECT DISTINCT date(played_at) AS day
        FROM listens
        WHERE played_at >= :start AND played_at < :end
        ORDER BY day ASC
        """,
        _range_params(date_range),
    )
    return [pd.to_datetime(v).date() for v in df["day"].tolist()] if not df.empty else []


def top_songs(date_range: DateRange, search: str = "", pagination: Pagination = Pagination()) -> pd.DataFrame:
    params = _range_params(date_range) | {
        "search": f"%{search.lower()}%",
        "limit": pagination.limit,
        "offset": pagination.offset,
    }
    return _fetch_df(
        """
        SELECT
          t.id,
          t.name,
          COALESCE(al.name, '') AS album_name,
          GROUP_CONCAT(ar.name, ', ') AS artists,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played), 0) / 60000.0 AS minutes,
          MAX(l.played_at) AS last_played
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        LEFT JOIN albums al ON al.id = t.album_id
        LEFT JOIN track_artists ta ON ta.track_id = t.id
        LEFT JOIN artists ar ON ar.id = ta.artist_id
        WHERE l.played_at >= :start AND l.played_at < :end
          AND lower(t.name) LIKE :search
        GROUP BY t.id, t.name, al.name
        ORDER BY minutes DESC, plays DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )


def top_artists(date_range: DateRange, search: str = "", pagination: Pagination = Pagination()) -> pd.DataFrame:
    params = _range_params(date_range) | {
        "search": f"%{search.lower()}%",
        "limit": pagination.limit,
        "offset": pagination.offset,
    }
    return _fetch_df(
        """
        SELECT
          ar.id,
          ar.name,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played), 0) / 60000.0 AS minutes,
          MAX(l.played_at) AS last_played
        FROM listens l
        JOIN track_artists ta ON ta.track_id = l.track_id
        JOIN artists ar ON ar.id = ta.artist_id
        WHERE l.played_at >= :start AND l.played_at < :end
          AND lower(ar.name) LIKE :search
        GROUP BY ar.id, ar.name
        ORDER BY minutes DESC, plays DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )


def top_albums(date_range: DateRange, search: str = "", pagination: Pagination = Pagination()) -> pd.DataFrame:
    params = _range_params(date_range) | {
        "search": f"%{search.lower()}%",
        "limit": pagination.limit,
        "offset": pagination.offset,
    }
    return _fetch_df(
        """
        SELECT
          al.id,
          al.name,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played), 0) / 60000.0 AS minutes,
          MAX(l.played_at) AS last_played
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        JOIN albums al ON al.id = t.album_id
        WHERE l.played_at >= :start AND l.played_at < :end
          AND lower(al.name) LIKE :search
        GROUP BY al.id, al.name
        ORDER BY minutes DESC, plays DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )


def top_genres(date_range: DateRange, pagination: Pagination = Pagination()) -> pd.DataFrame:
    params = _range_params(date_range) | {"limit": pagination.limit, "offset": pagination.offset}
    return _fetch_df(
        """
        SELECT
          g.name,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played), 0) / 60000.0 AS minutes
        FROM listens l
        JOIN track_artists ta ON ta.track_id = l.track_id
        JOIN artist_genres ag ON ag.artist_id = ta.artist_id
        JOIN genres g ON g.id = ag.genre_id
        WHERE l.played_at >= :start AND l.played_at < :end
        GROUP BY g.name
        ORDER BY minutes DESC, plays DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )


def daily_minutes(date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT date(played_at) AS day, COALESCE(SUM(ms_played),0)/60000.0 AS minutes, COUNT(*) AS plays
        FROM listens
        WHERE played_at >= :start AND played_at < :end
        GROUP BY date(played_at)
        ORDER BY day ASC
        """,
        _range_params(date_range),
    )


def hourly_distribution(date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT CAST(strftime('%H', played_at) AS INTEGER) AS hour,
               COALESCE(SUM(ms_played),0)/60000.0 AS minutes,
               COUNT(*) AS plays
        FROM listens
        WHERE played_at >= :start AND played_at < :end
        GROUP BY CAST(strftime('%H', played_at) AS INTEGER)
        ORDER BY hour ASC
        """,
        _range_params(date_range),
    )


def weekday_weekend(date_range: DateRange) -> dict[str, float]:
    df = _fetch_df(
        """
        SELECT
          SUM(CASE WHEN CAST(strftime('%w', played_at) AS INTEGER) BETWEEN 1 AND 5 THEN ms_played ELSE 0 END)/60000.0 AS weekday_minutes,
          SUM(CASE WHEN CAST(strftime('%w', played_at) AS INTEGER) IN (0,6) THEN ms_played ELSE 0 END)/60000.0 AS weekend_minutes
        FROM listens
        WHERE played_at >= :start AND played_at < :end
        """,
        _range_params(date_range),
    )
    if df.empty:
        return {"weekday_minutes": 0.0, "weekend_minutes": 0.0}
    row = df.iloc[0]
    return {
        "weekday_minutes": float(row["weekday_minutes"] or 0.0),
        "weekend_minutes": float(row["weekend_minutes"] or 0.0),
    }


def repeat_ratio(date_range: DateRange) -> float:
    df = _fetch_df(
        """
        WITH counts AS (
          SELECT track_id, COUNT(*) AS c
          FROM listens
          WHERE played_at >= :start AND played_at < :end
          GROUP BY track_id
        )
        SELECT
          COALESCE(SUM(CASE WHEN c > 1 THEN c ELSE 0 END),0) AS repeated_plays,
          COALESCE(SUM(c),0) AS total_plays
        FROM counts
        """,
        _range_params(date_range),
    )
    if df.empty:
        return 0.0
    row = df.iloc[0]
    repeated = float(row["repeated_plays"] or 0.0)
    total = float(row["total_plays"] or 0.0)
    return repeated / total if total else 0.0


def playlists(search: str = "") -> pd.DataFrame:
    with SessionLocal() as session:
        conn = session.connection()
        return pd.read_sql_query(
            text(
                """
                SELECT id, name, owner, snapshot_at
                FROM playlists
                WHERE lower(name) LIKE :search
                ORDER BY name ASC
                """
            ),
            conn,
            params={"search": f"%{search.lower()}%"},
        )


def playlist_tracks(playlist_id: str) -> pd.DataFrame:
    with SessionLocal() as session:
        conn = session.connection()
        return pd.read_sql_query(
            text(
                """
                SELECT t.id, t.name, COALESCE(al.name,'') AS album_name
                FROM playlist_tracks pt
                JOIN tracks t ON t.id = pt.track_id
                LEFT JOIN albums al ON al.id = t.album_id
                WHERE pt.playlist_id = :playlist_id
                ORDER BY pt.added_at DESC
                """
            ),
            conn,
            params={"playlist_id": playlist_id},
        )


def set_setting(key: str, value: str) -> None:
    with SessionLocal() as session:
        session.execute(
            text(
                """
                INSERT INTO app_settings(key, value, updated_at)
                VALUES(:key, :value, :updated_at)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """
            ),
            {"key": key, "value": value, "updated_at": datetime.now(UTC)},
        )
        session.commit()


def get_setting(key: str) -> str | None:
    with SessionLocal() as session:
        row = session.execute(text("SELECT value FROM app_settings WHERE key=:key"), {"key": key}).first()
    return row[0] if row else None


def refresh_daily_aggregate_for_day(target_day: date) -> None:
    start = datetime.combine(target_day, datetime.min.time())
    end = start + timedelta(days=1)
    with SessionLocal() as session:
        row = session.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(l.ms_played),0) / 60000.0 AS minutes,
                    COUNT(*) AS plays,
                    COUNT(DISTINCT l.track_id) AS unique_tracks,
                    COUNT(DISTINCT ta.artist_id) AS unique_artists,
                    COUNT(DISTINCT t.album_id) AS unique_albums
                FROM listens l
                LEFT JOIN track_artists ta ON ta.track_id = l.track_id
                LEFT JOIN tracks t ON t.id = l.track_id
                WHERE l.played_at >= :start AND l.played_at < :end
                """
            ),
            {"start": start, "end": end},
        ).first()

        minutes = int(row[0] or 0.0)
        plays = int(row[1] or 0)
        unique_tracks = int(row[2] or 0)
        unique_artists = int(row[3] or 0)
        unique_albums = int(row[4] or 0)

        session.execute(
            text(
                """
                INSERT INTO aggregates_daily(day, minutes, plays, unique_tracks, unique_artists, unique_albums)
                VALUES(:day, :minutes, :plays, :unique_tracks, :unique_artists, :unique_albums)
                ON CONFLICT(day) DO UPDATE SET
                    minutes=excluded.minutes,
                    plays=excluded.plays,
                    unique_tracks=excluded.unique_tracks,
                    unique_artists=excluded.unique_artists,
                    unique_albums=excluded.unique_albums
                """
            ),
            {
                "day": target_day,
                "minutes": minutes,
                "plays": plays,
                "unique_tracks": unique_tracks,
                "unique_artists": unique_artists,
                "unique_albums": unique_albums,
            },
        )
        session.commit()


def top_entities_for_dashboard(date_range: DateRange) -> tuple[pd.DataFrame, pd.DataFrame]:
    return top_artists(date_range, pagination=Pagination(limit=10)), top_songs(
        date_range, pagination=Pagination(limit=10)
    )


def song_daily_trend(track_id: str, date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT date(played_at) AS day, COUNT(*) AS plays, COALESCE(SUM(ms_played),0)/60000.0 AS minutes
        FROM listens
        WHERE track_id = :track_id
          AND played_at >= :start AND played_at < :end
        GROUP BY date(played_at)
        ORDER BY day ASC
        """,
        _range_params(date_range) | {"track_id": track_id},
    )


def artist_daily_trend(artist_id: str, date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT date(l.played_at) AS day, COUNT(*) AS plays, COALESCE(SUM(l.ms_played),0)/60000.0 AS minutes
        FROM listens l
        JOIN track_artists ta ON ta.track_id = l.track_id
        WHERE ta.artist_id = :artist_id
          AND l.played_at >= :start AND l.played_at < :end
        GROUP BY date(l.played_at)
        ORDER BY day ASC
        """,
        _range_params(date_range) | {"artist_id": artist_id},
    )


def album_daily_trend(album_id: str, date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT date(l.played_at) AS day, COUNT(*) AS plays, COALESCE(SUM(l.ms_played),0)/60000.0 AS minutes
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        WHERE t.album_id = :album_id
          AND l.played_at >= :start AND l.played_at < :end
        GROUP BY date(l.played_at)
        ORDER BY day ASC
        """,
        _range_params(date_range) | {"album_id": album_id},
    )


def genre_evolution(date_range: DateRange, bucket: str) -> pd.DataFrame:
    if bucket == "month":
        group_expr = "strftime('%Y-%m-01', l.played_at)"
    elif bucket == "week":
        group_expr = "date(l.played_at, '-' || ((strftime('%w', l.played_at) + 6) % 7) || ' days')"
    else:
        group_expr = "date(l.played_at)"

    sql = f"""
        SELECT {group_expr} AS bucket, g.name AS genre, COALESCE(SUM(l.ms_played),0)/60000.0 AS minutes
        FROM listens l
        JOIN track_artists ta ON ta.track_id = l.track_id
        JOIN artist_genres ag ON ag.artist_id = ta.artist_id
        JOIN genres g ON g.id = ag.genre_id
        WHERE l.played_at >= :start AND l.played_at < :end
        GROUP BY bucket, g.name
        ORDER BY bucket ASC, minutes DESC
    """
    return _fetch_df(sql, _range_params(date_range))


def obsession_candidates_songs(date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT
          t.id,
          t.name,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played),0) AS total_ms,
          COUNT(DISTINCT date(l.played_at)) AS active_days,
          MAX(l.played_at) AS last_played
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        WHERE l.played_at >= :start AND l.played_at < :end
        GROUP BY t.id, t.name
        HAVING COUNT(*) > 0
        ORDER BY total_ms DESC
        LIMIT 200
        """,
        _range_params(date_range),
    )


def obsession_candidates_artists(date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT
          a.id,
          a.name,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played),0) AS total_ms,
          COUNT(DISTINCT date(l.played_at)) AS active_days,
          MAX(l.played_at) AS last_played
        FROM listens l
        JOIN track_artists ta ON ta.track_id = l.track_id
        JOIN artists a ON a.id = ta.artist_id
        WHERE l.played_at >= :start AND l.played_at < :end
        GROUP BY a.id, a.name
        HAVING COUNT(*) > 0
        ORDER BY total_ms DESC
        LIMIT 200
        """,
        _range_params(date_range),
    )


def obsession_candidates_albums(date_range: DateRange) -> pd.DataFrame:
    return _fetch_df(
        """
        SELECT
          al.id,
          al.name,
          COUNT(*) AS plays,
          COALESCE(SUM(l.ms_played),0) AS total_ms,
          COUNT(DISTINCT date(l.played_at)) AS active_days,
          MAX(l.played_at) AS last_played
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        JOIN albums al ON al.id = t.album_id
        WHERE l.played_at >= :start AND l.played_at < :end
        GROUP BY al.id, al.name
        HAVING COUNT(*) > 0
        ORDER BY total_ms DESC
        LIMIT 200
        """,
        _range_params(date_range),
    )


def latest_listen() -> dict[str, Any] | None:
    df = _fetch_df(
        """
        SELECT t.name AS track_name,
               COALESCE(al.name,'') AS album_name,
               GROUP_CONCAT(ar.name, ', ') AS artists,
               l.played_at
        FROM listens l
        JOIN tracks t ON t.id = l.track_id
        LEFT JOIN albums al ON al.id = t.album_id
        LEFT JOIN track_artists ta ON ta.track_id = t.id
        LEFT JOIN artists ar ON ar.id = ta.artist_id
        GROUP BY l.id, t.name, al.name, l.played_at
        ORDER BY l.played_at DESC
        LIMIT 1
        """,
        {},
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()
