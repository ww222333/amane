"""library_tvshow_and_episode_nfo_templates

Revision ID: f4390388d385
Revises: 62a1c05d1bac
Create Date: 2026-10-14 12:10:39.760002
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "f4390388d385"
down_revision: str | None = "62a1c05d1bac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.add_column(sa.Column("tvshow_nfo_template", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column("episode_nfo_template", sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.drop_column("episode_nfo_template")
        batch_op.drop_column("tvshow_nfo_template")
