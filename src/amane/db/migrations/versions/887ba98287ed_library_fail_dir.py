"""library_fail_dir

Revision ID: 887ba98287ed
Revises: e6c559a3f203
Create Date: 2026-09-12 15:53:33.218553
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "887ba98287ed"
down_revision: str | None = "e6c559a3f203"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.add_column(sa.Column("fail_dir", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("move_to_fail_dir", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("exclude_fail_dir", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.drop_column("exclude_fail_dir")
        batch_op.drop_column("move_to_fail_dir")
        batch_op.drop_column("fail_dir")
