"""add_email_sent_fields_to_invitation_codes

Revision ID: add_email_sent_001
Revises: dbb1c0220ee1
Create Date: 2026-01-14 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_email_sent_001'
down_revision: Union[str, Sequence[str], None] = 'add_member_role_inv'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email_sent_to and email_sent_at columns to invitation_codes table."""
    
    # Use idempotent SQL to check if columns exist before adding
    conn = op.get_bind()
    
    # Check if email_sent_to column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'email_sent_to'
        )
    """))
    if not result.scalar():
        op.add_column('invitation_codes', sa.Column('email_sent_to', sa.String(), nullable=True))
    
    # Check if email_sent_at column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'email_sent_at'
        )
    """))
    if not result.scalar():
        op.add_column('invitation_codes', sa.Column('email_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove email_sent_to and email_sent_at columns from invitation_codes table."""
    op.drop_column('invitation_codes', 'email_sent_at')
    op.drop_column('invitation_codes', 'email_sent_to')
