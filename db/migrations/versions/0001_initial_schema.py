"""Initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-02-14 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "albums",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("release_date", sa.String(length=20), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "artists",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "playlists",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "aggregates_daily",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("minutes", sa.BigInteger(), nullable=False),
        sa.Column("plays", sa.Integer(), nullable=False),
        sa.Column("unique_tracks", sa.Integer(), nullable=False),
        sa.Column("unique_artists", sa.Integer(), nullable=False),
        sa.Column("unique_albums", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("day"),
    )
    op.create_index("ix_aggregates_daily_day", "aggregates_daily", ["day"], unique=False)

    op.create_table(
        "tracks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("album_id", sa.String(length=64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("explicit", sa.Boolean(), nullable=True),
        sa.Column("popularity", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tracks_album_id", "tracks", ["album_id"], unique=False)

    op.create_table(
        "artist_genres",
        sa.Column("artist_id", sa.String(length=64), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"]),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.PrimaryKeyConstraint("artist_id", "genre_id"),
    )
    op.create_index("ix_artist_genres_artist_id", "artist_genres", ["artist_id"], unique=False)

    op.create_table(
        "track_artists",
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("artist_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"]),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("track_id", "artist_id"),
    )
    op.create_index("ix_track_artists_track_id", "track_artists", ["track_id"], unique=False)

    op.create_table(
        "playlist_tracks",
        sa.Column("playlist_id", sa.String(length=64), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"]),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("playlist_id", "track_id"),
    )

    op.create_table(
        "listens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ms_played", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("context_type", sa.String(length=40), nullable=True),
        sa.Column("context_id", sa.String(length=128), nullable=True),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("played_at", "track_id", "ms_played", name="uq_listen_dedupe"),
    )
    op.create_index("ix_listens_context", "listens", ["context_type", "context_id"], unique=False)
    op.create_index("ix_listens_played_at", "listens", ["played_at"], unique=False)
    op.create_index("ix_listens_track_id", "listens", ["track_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listens_track_id", table_name="listens")
    op.drop_index("ix_listens_played_at", table_name="listens")
    op.drop_index("ix_listens_context", table_name="listens")
    op.drop_table("listens")
    op.drop_table("playlist_tracks")
    op.drop_index("ix_track_artists_track_id", table_name="track_artists")
    op.drop_table("track_artists")
    op.drop_index("ix_artist_genres_artist_id", table_name="artist_genres")
    op.drop_table("artist_genres")
    op.drop_index("ix_tracks_album_id", table_name="tracks")
    op.drop_table("tracks")
    op.drop_index("ix_aggregates_daily_day", table_name="aggregates_daily")
    op.drop_table("aggregates_daily")
    op.drop_table("playlists")
    op.drop_table("genres")
    op.drop_table("artists")
    op.drop_table("albums")
