"""merge_heads

Revision ID: 5f02dca46f48
Revises: b5a87a5ee86e, e3f4a5b6c7d8
Create Date: 2026-01-09 14:34:05.644560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f02dca46f48'
down_revision: Union[str, Sequence[str], None] = ('b5a87a5ee86e', 'e3f4a5b6c7d8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
