"""episodes_table_and_media_file_episode_id

Revision ID: 62a1c05d1bac
Revises: fdd597ef57cc
Create Date: 2026-10-14 11:20:33.925256
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "62a1c05d1bac"
down_revision: str | None = "fdd597ef57cc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metadata_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("episode", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("plot", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column("updated_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["metadata_id"], ["metadata.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metadata_id", "season", "episode", name="uq_episodes_metadata_season_episode"),
    )
    op.create_index(op.f("ix_episodes_metadata_id"), "episodes", ["metadata_id"], unique=False)
    with op.batch_alter_table("media_files") as batch_op:
        batch_op.add_column(sa.Column("episode_id", sa.Integer(), nullable=True))
        batch_op.create_index(op.f("ix_media_files_episode_id"), ["episode_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_media_files_episode_id_episodes",
            "episodes",
            ["episode_id"],
            ["id"],
        )
    op.add_column("metadata", sa.Column("episode_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("metadata", "episode_count")
    with op.batch_alter_table("media_files") as batch_op:
        batch_op.drop_constraint("fk_media_files_episode_id_episodes", type_="foreignkey")
        batch_op.drop_index(op.f("ix_media_files_episode_id"))
        batch_op.drop_column("episode_id")
    op.drop_index(op.f("ix_episodes_metadata_id"), table_name="episodes")
    op.drop_table("episodes")
