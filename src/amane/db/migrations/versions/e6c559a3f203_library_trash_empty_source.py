"""library_trash_empty_source

Revision ID: e6c559a3f203
Revises: 022f8eb0d22f
Create Date: 2026-09-12 15:01:57.198603
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e6c559a3f203"
down_revision: str | None = "022f8eb0d22f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.add_column(
            sa.Column("trash_empty_source", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.drop_column("trash_empty_source")
