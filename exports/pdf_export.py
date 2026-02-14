from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle

from analytics.date_ranges import DateRange
from db.repository import top_albums, top_artists, top_genres, top_songs


def _table_for_entity(entity: str, date_range: DateRange) -> tuple[list[str], list[list[str]]]:
    if entity == "songs":
        df = top_songs(date_range).head(20)
        cols = ["name", "artists", "plays", "minutes"]
    elif entity == "artists":
        df = top_artists(date_range).head(20)
        cols = ["name", "plays", "minutes"]
    elif entity == "albums":
        df = top_albums(date_range).head(20)
        cols = ["name", "plays", "minutes"]
    elif entity == "genres":
        df = top_genres(date_range).head(20)
        cols = ["name", "plays", "minutes"]
    else:
        raise ValueError(f"Unsupported entity for PDF export: {entity}")

    rows = [[str(row[col]) for col in cols] for _, row in df.iterrows()]
    return cols, rows


def export_rankings_pdf(entity: str, date_range: DateRange) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    title = Paragraph(f"Spotify Stats Report: {entity.title()}", styles["Title"])
    subtitle = Paragraph(
        f"Range: {date_range.start.isoformat()} to {date_range.end.isoformat()}",
        styles["Normal"],
    )

    cols, rows = _table_for_entity(entity, date_range)
    data = [cols] + rows if rows else [cols, ["No data", "", "", ""][: len(cols)]]
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1db954")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    story = [title, Spacer(1, 8), subtitle, Spacer(1, 12), table]
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
