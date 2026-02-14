# spotify2

Local-first Spotify Stats app in Python (Streamlit + SQLite) with Spotify OAuth, incremental sync, historical import, analytics, and exports.

## Implemented
- Reference UX parity map: `docs/REFERENCE_PARITY.md`
- Global date filter (presets + custom) persisted across tabs/pages
- Navigation pages:
  - Dashboard
  - Insights
  - Obsessed
  - Playlists
  - Artists
  - Songs
  - Albums
  - Genres
  - Listening Diversity Score
  - Genre Evolution
  - Wrapped Clone
  - Settings
- Spotify OAuth Authorization Code flow (Spotipy)
- Encrypted token storage at rest (Fernet, DB-backed cache)
- API sync: recently played incremental ingest
- Historical import: Extended Streaming History JSON files
- Dedupe logic for listens (`played_at + track_id + ms tolerance`)
- Daily aggregate maintenance (`aggregates_daily`)
- CSV and PDF export for filtered rankings
- Demo mode data loader
- Unit tests for date filters, streaks, diversity, obsession, daily aggregates

## Quick start

1. Install dependencies
```bash
make install
```

2. Configure environment
```bash
cp .env.example .env
```

3. Set required env vars in `.env`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI` (default `http://localhost:8501`)
- `FERNET_KEY` (generate below)

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Initialize DB
```bash
make init-db
# or migrations:
make migrate
```

5. Run app
```bash
make run
```

6. In app `Settings`:
- Connect Spotify
- Sync recently played
- Import history JSON files
- Export CSV/PDF

## Environment variables
- `DATABASE_URL` (default: `sqlite:///spotify_stats.db`)
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `FERNET_KEY`
- `OPENAI_API_KEY` (optional)
- `ANTHROPIC_API_KEY` (optional)

## Dev commands
```bash
make test
make lint
```

## Repository layout
- `app/` Streamlit app, navigation, page rendering, global filter
- `db/` SQLAlchemy models/session/repository/migrations
- `spotify/` OAuth, API client, sync/import pipeline, metadata resolver
- `analytics/` date ranges, streak/diversity/obsession/insight/wrapped logic
- `exports/` CSV/PDF exports
- `tests/` pytest tests
- `docs/` parity and design docs
