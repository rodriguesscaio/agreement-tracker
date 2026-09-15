"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agreements",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("source_text_excerpt", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("commitment", sa.Text(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column(
            "confidence",
            sa.Enum("high", "medium", "low", name="confidence_level"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "resolved", name="agreement_status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("agreements")
    sa.Enum(name="confidence_level").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="agreement_status").drop(op.get_bind(), checkfirst=True)
