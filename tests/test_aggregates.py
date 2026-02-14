from datetime import UTC, date, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from db.models import Base
from db.repository import refresh_daily_aggregate_for_day


def test_refresh_daily_aggregate_for_day(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setattr("db.repository.SessionLocal", TestingSessionLocal)

    with TestingSessionLocal() as session:
        session.execute(text("INSERT INTO albums(id, name) VALUES('alb1', 'Album 1')"))
        session.execute(text("INSERT INTO tracks(id, name, album_id) VALUES('trk1', 'Track 1', 'alb1')"))
        session.execute(text("INSERT INTO artists(id, name) VALUES('art1', 'Artist 1')"))
        session.execute(text("INSERT INTO track_artists(track_id, artist_id) VALUES('trk1', 'art1')"))
        session.execute(
            text(
                """
                INSERT INTO listens(played_at, ms_played, track_id, context_type, context_id, device_name)
                VALUES(:played_at, :ms_played, 'trk1', NULL, NULL, NULL)
                """
            ),
            {
                "played_at": datetime(2026, 2, 14, 9, 0, tzinfo=UTC),
                "ms_played": 180000,
            },
        )
        session.commit()

    refresh_daily_aggregate_for_day(date(2026, 2, 14))

    with TestingSessionLocal() as session:
        row = session.execute(
            text(
                """
                SELECT minutes, plays, unique_tracks, unique_artists, unique_albums
                FROM aggregates_daily
                WHERE day = '2026-02-14'
                """
            )
        ).first()

    assert row is not None
    assert row[0] == 3
    assert row[1] == 1
    assert row[2] == 1
    assert row[3] == 1
    assert row[4] == 1
