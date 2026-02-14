"""Add OAuth token storage table

Revision ID: 0002_oauth_tokens
Revises: 0001_initial_schema
Create Date: 2026-02-14 00:10:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_oauth_tokens"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oauth_tokens",
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("token_encrypted", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("provider"),
    )


def downgrade() -> None:
    op.drop_table("oauth_tokens")
