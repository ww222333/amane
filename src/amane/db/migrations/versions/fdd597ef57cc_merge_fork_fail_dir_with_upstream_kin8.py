"""merge fork fail_dir head with upstream kin8 reproject

Revision ID: fdd597ef57cc
Revises: 836b567fc54c, 8dbd0fa0905e
Create Date: 2026-10-13 15:31:12.750236
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "fdd597ef57cc"
down_revision: str | tuple[str, ...] | None = ("836b567fc54c", "8dbd0fa0905e")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
