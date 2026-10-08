"""merge fork library columns with upstream heads

Revision ID: 836b567fc54c
Revises: 1f050b272f7d, 887ba98287ed
Create Date: 2026-10-08 18:21:53.633295
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "836b567fc54c"
down_revision: str | tuple[str, ...] | None = ("1f050b272f7d", "887ba98287ed")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
