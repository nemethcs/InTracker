"""add member_role to invitation_codes

Revision ID: add_member_role_inv
Revises: 10ce72dec47c
Create Date: 2026-01-14 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_member_role_inv'
down_revision: Union[str, Sequence[str], None] = '10ce72dec47c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add member_role column to invitation_codes table
    # Default value is 'member' for existing invitations
    op.add_column('invitation_codes', sa.Column('member_role', sa.String(), nullable=False, server_default='member'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove member_role column from invitation_codes table
    op.drop_column('invitation_codes', 'member_role')
