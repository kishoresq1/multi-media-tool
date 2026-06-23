"""Add marketing usage columns to unified_intel.

Revision ID: 002
Revises: 001
Create Date: 2026-06-23 00:00:00.000000

Requirements: 1.5, 6.1
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


TABLE_NAME = "unified_intel"
USED_INDEX_NAME = "ix_unified_intel_used_in_marketing"


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    return any(
        column["name"] == column_name
        for column in _inspector().get_columns(table_name)
    )


def _has_index(table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def upgrade() -> None:
    if not _has_table(TABLE_NAME):
        raise RuntimeError(f"Expected table {TABLE_NAME!r} to exist before migration 002")

    if not _has_column(TABLE_NAME, "used_in_marketing"):
        op.add_column(
            TABLE_NAME,
            sa.Column(
                "used_in_marketing",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    if not _has_column(TABLE_NAME, "used_at"):
        op.add_column(
            TABLE_NAME,
            sa.Column(
                "used_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

    if not _has_index(TABLE_NAME, USED_INDEX_NAME):
        op.create_index(
            USED_INDEX_NAME,
            TABLE_NAME,
            ["used_in_marketing"],
        )


def downgrade() -> None:
    if not _has_table(TABLE_NAME):
        return

    if _has_index(TABLE_NAME, USED_INDEX_NAME):
        op.drop_index(USED_INDEX_NAME, table_name=TABLE_NAME)

    if _has_column(TABLE_NAME, "used_at"):
        op.drop_column(TABLE_NAME, "used_at")

    if _has_column(TABLE_NAME, "used_in_marketing"):
        op.drop_column(TABLE_NAME, "used_in_marketing")
