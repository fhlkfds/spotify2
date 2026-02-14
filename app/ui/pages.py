from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics.date_ranges import DateRange as AnalyticsDateRange
from analytics.date_ranges import bucket_for_range, previous_period
from analytics.diversity import diversity_score
from analytics.insights import render_insight_text
from analytics.metrics import consecutive_streak, current_streak_to_today
from analytics.obsession import obsession_score
from analytics.wrapped import classify_era
from app.types import DateRange
from app.ui.components import empty_state, metric_row
from app.ui.settings import render_settings_page
from db.repository import (
    Pagination,
    album_daily_trend,
    artist_daily_trend,
    daily_minutes,
    genre_evolution,
    get_kpis,
    hourly_distribution,
    latest_listen,
    listened_days,
    obsession_candidates_albums,
    obsession_candidates_artists,
    obsession_candidates_songs,
    playlist_tracks,
    playlists,
    repeat_ratio,
    song_daily_trend,
    top_albums,
    top_artists,
    top_entities_for_dashboard,
    top_genres,
    top_songs,
    weekday_weekend,
)
from spotify.client import current_playing


def _to_analytics_range(date_range: DateRange) -> AnalyticsDateRange:
    return AnalyticsDateRange(start=date_range.start, end=date_range.end, label=date_range.label)


@st.cache_data(ttl=60)
def _cached_kpis(start: date, end: date) -> dict[str, float]:
    return get_kpis(AnalyticsDateRange(start=start, end=end, label="cached"))


@st.cache_data(ttl=60)
def _cached_daily(start: date, end: date) -> pd.DataFrame:
    return daily_minutes(AnalyticsDateRange(start=start, end=end, label="cached"))


@st.cache_data(ttl=60)
def _cached_top(start: date, end: date) -> tuple[pd.DataFrame, pd.DataFrame]:
    return top_entities_for_dashboard(AnalyticsDateRange(start=start, end=end, label="cached"))


@st.cache_data(ttl=15)
def _cached_now_playing() -> dict | None:
    return current_playing()


def render_page(page_key: str, date_range: DateRange) -> None:
    if page_key == "dashboard":
        _render_dashboard(date_range)
    elif page_key == "insights":
        _render_insights(date_range)
    elif page_key == "obsessed":
        _render_obsessed(date_range)
    elif page_key == "playlists":
        _render_playlists(date_range)
    elif page_key == "artists":
        _render_artists(date_range)
    elif page_key == "songs":
        _render_songs(date_range)
    elif page_key == "albums":
        _render_albums(date_range)
    elif page_key == "genres":
        _render_genres(date_range)
    elif page_key == "diversity":
        _render_diversity(date_range)
    elif page_key == "genre_evolution":
        _render_genre_evolution(date_range)
    elif page_key == "wrapped":
        _render_wrapped(date_range)
    elif page_key == "settings":
        render_settings_page(_to_analytics_range(date_range))
    else:
        st.title("Spotify Stats")


def _render_dashboard(date_range: DateRange) -> None:
    st.title("Dashboard")
    st.caption(f"{date_range.start.isoformat()} to {date_range.end.isoformat()}")

    analytics_range = _to_analytics_range(date_range)
    kpis = _cached_kpis(date_range.start, date_range.end)
    days = listened_days(analytics_range)
    streak = consecutive_streak(days)
    current_streak = current_streak_to_today(days) if date_range.end >= date.today() else 0

    metric_row(
        [
            ("Total time listened", f"{kpis['total_minutes'] / 60:.1f} h", None),
            ("Unique artists", f"{kpis['unique_artists']}", None),
            ("Unique albums", f"{kpis['unique_albums']}", None),
            ("Unique songs", f"{kpis['unique_songs']}", None),
            ("Listening streak", f"{streak} days", f"Current {current_streak} days" if current_streak else None),
        ]
    )

    now = _cached_now_playing()
    with st.container(border=True):
        st.subheader("Currently listening")
        if now and now.get("is_playing"):
            item = now.get("item") or {}
            artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
            progress = now.get("progress_ms") or 0
            duration = item.get("duration_ms") or 1
            st.write(f"**{item.get('name', 'Unknown')}** - {artists}")
            st.progress(min(progress / duration, 1.0))
            device = (now.get("device") or {}).get("name")
            if device:
                st.caption(f"Device: {device}")
        else:
            last = latest_listen()
            if last:
                st.write("Not currently playing. Last played:")
                st.write(f"**{last['track_name']}** - {last.get('artists', '')}")
                st.caption(str(last.get("played_at")))
            else:
                empty_state("Not currently playing and no history found.")

    top_art, top_song = _cached_top(date_range.start, date_range.end)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top artists")
        if top_art.empty:
            empty_state("No artist data for selected range.")
        else:
            fig = px.bar(top_art.head(10), x="minutes", y="name", orientation="h")
            fig.update_layout(height=350, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Top songs")
        if top_song.empty:
            empty_state("No song data for selected range.")
        else:
            fig = px.bar(top_song.head(10), x="minutes", y="name", orientation="h")
            fig.update_layout(height=350, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Listening heatmap")
    daily = _cached_daily(date_range.start, date_range.end)
    if daily.empty:
        empty_state("No daily listening data.")
    else:
        daily["day"] = pd.to_datetime(daily["day"])
        daily["weekday"] = daily["day"].dt.weekday
        daily["week"] = daily["day"].dt.isocalendar().week.astype(int)
        pivot = daily.pivot_table(index="weekday", columns="week", values="minutes", fill_value=0)
        fig = px.imshow(pivot, aspect="auto", labels={"x": "ISO Week", "y": "Weekday", "color": "Minutes"})
        st.plotly_chart(fig, use_container_width=True)


def _render_insights(date_range: DateRange) -> None:
    st.title("Insights")
    analytics_range = _to_analytics_range(date_range)
    prev = previous_period(analytics_range)

    kpis = get_kpis(analytics_range)
    prev_kpis = get_kpis(prev)
    hours = hourly_distribution(analytics_range)
    week_split = weekday_weekend(analytics_range)
    genres = top_genres(analytics_range, Pagination(limit=10))
    rpt = repeat_ratio(analytics_range)

    if not hours.empty:
        fig = px.bar(hours, x="hour", y="minutes", title="Peak listening hours")
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(
            pd.DataFrame(
                {
                    "type": ["Weekday", "Weekend"],
                    "minutes": [week_split["weekday_minutes"], week_split["weekend_minutes"]],
                }
            ),
            names="type",
            values="minutes",
            title="Weekday vs Weekend",
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        if not genres.empty:
            fig = px.bar(genres, x="minutes", y="name", orientation="h", title="Top genres")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("No genre data available yet. Genre enrichment depends on artist metadata.")

    summary = {
        "peak_hour": float(hours.loc[hours["minutes"].idxmax(), "hour"]) if not hours.empty else 0,
        "weekday_minutes": week_split["weekday_minutes"],
        "weekend_minutes": week_split["weekend_minutes"],
        "repeat_ratio": rpt,
        "minutes": kpis["total_minutes"],
        "plays": kpis["plays"],
    }
    previous_summary = {"minutes": prev_kpis["total_minutes"], "plays": prev_kpis["plays"]}

    st.subheader("Smart Insights")
    for line in render_insight_text(summary, previous_summary):
        st.write(f"- {line}")


def _best_obsession(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    temp = df.copy()
    temp["last_played"] = pd.to_datetime(temp["last_played"], errors="coerce")
    now = pd.Timestamp.utcnow()
    temp["recency_days"] = (now - temp["last_played"]).dt.days.fillna(365).clip(lower=0)
    temp["repeat_density"] = temp["plays"] / temp["active_days"].replace(0, 1)
    temp["repeat_density"] = (temp["repeat_density"] / temp["repeat_density"].max()).fillna(0)
    temp["score"] = temp.apply(
        lambda r: obsession_score(
            int(r["plays"]),
            int(r["total_ms"]),
            float(r["repeat_density"]),
            int(r["recency_days"]),
        ),
        axis=1,
    )
    return temp.sort_values("score", ascending=False).iloc[0]


def _render_obsessed(date_range: DateRange) -> None:
    st.title("Obsessed")
    st.caption("obsession_score = 35% plays + 25% total_ms + 20% repeat_density + 20% recency")

    analytics_range = _to_analytics_range(date_range)
    best_song = _best_obsession(obsession_candidates_songs(analytics_range))
    best_artist = _best_obsession(obsession_candidates_artists(analytics_range))
    best_album = _best_obsession(obsession_candidates_albums(analytics_range))

    cols = st.columns(3)
    with cols[0]:
        st.subheader("Song")
        if best_song is not None:
            st.metric(best_song["name"], f"{best_song['score']:.1f}")
            st.caption(f"Plays: {int(best_song['plays'])} | Minutes: {int(best_song['total_ms']) / 60000:.1f}")
        else:
            empty_state("No song data.")
    with cols[1]:
        st.subheader("Artist")
        if best_artist is not None:
            st.metric(best_artist["name"], f"{best_artist['score']:.1f}")
            st.caption(f"Plays: {int(best_artist['plays'])} | Minutes: {int(best_artist['total_ms']) / 60000:.1f}")
        else:
            empty_state("No artist data.")
    with cols[2]:
        st.subheader("Album")
        if best_album is not None:
            st.metric(best_album["name"], f"{best_album['score']:.1f}")
            st.caption(f"Plays: {int(best_album['plays'])} | Minutes: {int(best_album['total_ms']) / 60000:.1f}")
        else:
            empty_state("No album data.")


def _render_playlists(date_range: DateRange) -> None:
    st.title("Playlists")
    st.caption("Search playlists and inspect snapshot tracks.")
    search = st.text_input("Search playlists")
    df = playlists(search=search)
    if df.empty:
        empty_state("No playlists found. Sync playlists from Spotify in Settings.")
        return

    st.dataframe(df, use_container_width=True)
    selected = st.selectbox("Select playlist", options=df["id"].tolist(), format_func=lambda x: df[df["id"] == x]["name"].iloc[0])
    tracks_df = playlist_tracks(selected)
    st.subheader("Playlist snapshot tracks")
    if tracks_df.empty:
        empty_state("No track snapshot data for this playlist.")
    else:
        st.dataframe(tracks_df, use_container_width=True)


def _render_artists(date_range: DateRange) -> None:
    st.title("Artists")
    query = st.text_input("Search artists")
    page = st.number_input("Page", min_value=1, value=1, step=1)
    df = top_artists(_to_analytics_range(date_range), search=query, pagination=Pagination(limit=50, offset=(page - 1) * 50))
    if df.empty:
        empty_state("No artist results.")
        return
    st.dataframe(df, use_container_width=True)
    selected = st.selectbox("Artist drill-down", options=df["id"].tolist(), format_func=lambda x: df[df["id"] == x]["name"].iloc[0])
    trend = artist_daily_trend(selected, _to_analytics_range(date_range))
    if not trend.empty:
        fig = px.line(trend, x="day", y="minutes", markers=True, title="Artist trend over time")
        st.plotly_chart(fig, use_container_width=True)


def _render_songs(date_range: DateRange) -> None:
    st.title("Songs")
    query = st.text_input("Search songs")
    page = st.number_input("Page ", min_value=1, value=1, step=1)
    df = top_songs(_to_analytics_range(date_range), search=query, pagination=Pagination(limit=50, offset=(page - 1) * 50))
    if df.empty:
        empty_state("No song results.")
        return
    st.dataframe(df, use_container_width=True)
    selected = st.selectbox("Song drill-down", options=df["id"].tolist(), format_func=lambda x: df[df["id"] == x]["name"].iloc[0])
    trend = song_daily_trend(selected, _to_analytics_range(date_range))
    if not trend.empty:
        fig = px.line(trend, x="day", y="minutes", markers=True, title="Song trend over time")
        st.plotly_chart(fig, use_container_width=True)


def _render_albums(date_range: DateRange) -> None:
    st.title("Albums")
    query = st.text_input("Search albums")
    page = st.number_input("Page  ", min_value=1, value=1, step=1)
    df = top_albums(_to_analytics_range(date_range), search=query, pagination=Pagination(limit=50, offset=(page - 1) * 50))
    if df.empty:
        empty_state("No album results.")
        return
    st.dataframe(df, use_container_width=True)
    selected = st.selectbox("Album drill-down", options=df["id"].tolist(), format_func=lambda x: df[df["id"] == x]["name"].iloc[0])
    trend = album_daily_trend(selected, _to_analytics_range(date_range))
    if not trend.empty:
        fig = px.line(trend, x="day", y="minutes", markers=True, title="Album trend over time")
        st.plotly_chart(fig, use_container_width=True)


def _render_genres(date_range: DateRange) -> None:
    st.title("Genres")
    df = top_genres(_to_analytics_range(date_range), pagination=Pagination(limit=200))
    if df.empty:
        empty_state("No genres found. Run Spotify sync to fetch artist genres.")
        return
    st.dataframe(df, use_container_width=True)
    fig = px.bar(df.head(20), x="minutes", y="name", orientation="h", title="Genre ranking")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)


def _render_diversity(date_range: DateRange) -> None:
    st.title("Listening Diversity Score")
    genres = top_genres(_to_analytics_range(date_range), pagination=Pagination(limit=200))
    artists = top_artists(_to_analytics_range(date_range), pagination=Pagination(limit=200))
    result = diversity_score(
        genre_minutes=genres["minutes"].tolist() if not genres.empty else [],
        artist_minutes=artists["minutes"].tolist() if not artists.empty else [],
    )
    st.metric("Diversity score", f"{result['score']:.1f}/100")
    st.write(f"Genre entropy component: {result['genre_component']:.1f}")
    st.write(f"Artist entropy component: {result['artist_component']:.1f}")


def _render_genre_evolution(date_range: DateRange) -> None:
    st.title("Genre Evolution")
    analytics_range = _to_analytics_range(date_range)
    bucket = bucket_for_range(analytics_range)
    df = genre_evolution(analytics_range, bucket=bucket)
    if df.empty:
        empty_state("No genre trend data available.")
        return
    top_genre_names = (
        df.groupby("genre")["minutes"].sum().sort_values(ascending=False).head(8).index.tolist()
    )
    filtered = df[df["genre"].isin(top_genre_names)]
    fig = px.area(filtered, x="bucket", y="minutes", color="genre", title=f"Genre share over time ({bucket})")
    st.plotly_chart(fig, use_container_width=True)


def _render_wrapped(date_range: DateRange) -> None:
    st.title("Wrapped Clone")
    analytics_range = _to_analytics_range(date_range)
    kpis = get_kpis(analytics_range)
    top_artist_df = top_artists(analytics_range, pagination=Pagination(limit=1))
    top_song_df = top_songs(analytics_range, pagination=Pagination(limit=1))
    top_genre_df = top_genres(analytics_range, pagination=Pagination(limit=1))
    rpt = repeat_ratio(analytics_range)

    top_artist = top_artist_df.iloc[0]["name"] if not top_artist_df.empty else "N/A"
    top_song = top_song_df.iloc[0]["name"] if not top_song_df.empty else "N/A"
    top_genre = top_genre_df.iloc[0]["name"] if not top_genre_df.empty else "N/A"

    era = classify_era(kpis["total_minutes"], int(kpis["unique_artists"]), rpt)

    metric_row(
        [
            ("Top artist", top_artist, None),
            ("Top song", top_song, None),
            ("Top genre", top_genre, None),
            ("Hours listened", f"{kpis['total_minutes'] / 60:.1f}", None),
        ]
    )
    st.subheader("Your listening era")
    st.success(era)
