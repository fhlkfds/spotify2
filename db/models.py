from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Listen(Base):
    __tablename__ = "listens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ms_played: Mapped[int] = mapped_column(Integer, nullable=False)
    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"), nullable=False, index=True)
    context_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    context_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_listens_context", "context_type", "context_id"),
        UniqueConstraint("played_at", "track_id", "ms_played", name="uq_listen_dedupe"),
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    album_id: Mapped[str | None] = mapped_column(ForeignKey("albums.id"), nullable=True, index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explicit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    popularity: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    release_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class TrackArtist(Base):
    __tablename__ = "track_artists"

    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"), primary_key=True)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), primary_key=True)

    __table_args__ = (Index("ix_track_artists_track_id", "track_id"),)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class ArtistGenre(Base):
    __tablename__ = "artist_genres"

    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)

    __table_args__ = (Index("ix_artist_genres_artist_id", "artist_id"),)


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_id: Mapped[str] = mapped_column(ForeignKey("playlists.id"), primary_key=True)
    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"), primary_key=True)
    added_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AggregateDaily(Base):
    __tablename__ = "aggregates_daily"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    minutes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    plays: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_tracks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_artists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_albums: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_aggregates_daily_day", "day"),)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
