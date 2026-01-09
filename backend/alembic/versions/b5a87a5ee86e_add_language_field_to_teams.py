"""add_language_field_to_teams

Revision ID: b5a87a5ee86e
Revises: 8be276c52a41
Create Date: 2026-01-08 17:59:43.673059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5a87a5ee86e'
down_revision: Union[str, Sequence[str], None] = '8be276c52a41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add language field to teams table
    # Language is nullable to support existing teams
    # Valid values: 'hu' (Hungarian) or 'en' (English)
    # Once set, it cannot be changed (enforced at application level)
    op.add_column('teams', sa.Column('language', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove language field from teams table
    op.drop_column('teams', 'language')
