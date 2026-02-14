"""Add app settings table

Revision ID: 0003_app_settings
Revises: 0002_oauth_tokens
Create Date: 2026-02-14 00:20:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_app_settings"
down_revision = "0002_oauth_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
