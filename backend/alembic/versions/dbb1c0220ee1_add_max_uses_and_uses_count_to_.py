"""add_max_uses_and_uses_count_to_invitation_codes

Revision ID: dbb1c0220ee1
Revises: fix_audit_001
Create Date: 2026-01-12 12:19:35.989211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbb1c0220ee1'
down_revision: Union[str, Sequence[str], None] = 'fix_audit_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add max_uses, uses_count, is_active, and updated_at columns to invitation_codes table."""
    
    # Use idempotent SQL to check if columns exist before adding
    conn = op.get_bind()
    
    # Check if max_uses column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'max_uses'
        )
    """))
    max_uses_exists = result.scalar()
    
    if not max_uses_exists:
        op.add_column('invitation_codes', 
            sa.Column('max_uses', sa.Integer(), nullable=True, comment='None = unlimited')
        )
    
    # Check if uses_count column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'uses_count'
        )
    """))
    uses_count_exists = result.scalar()
    
    if not uses_count_exists:
        op.add_column('invitation_codes',
            sa.Column('uses_count', sa.Integer(), server_default='0', nullable=False)
        )
        # Set default value for existing rows
        op.execute("UPDATE invitation_codes SET uses_count = 0 WHERE uses_count IS NULL")
    
    # Check if is_active column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'is_active'
        )
    """))
    is_active_exists = result.scalar()
    
    if not is_active_exists:
        op.add_column('invitation_codes',
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False)
        )
        # Set default value for existing rows
        op.execute("UPDATE invitation_codes SET is_active = true WHERE is_active IS NULL")
    
    # Check if updated_at column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'updated_at'
        )
    """))
    updated_at_exists = result.scalar()
    
    if not updated_at_exists:
        op.add_column('invitation_codes',
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False)
        )
        # Set default value for existing rows
        op.execute("UPDATE invitation_codes SET updated_at = NOW() WHERE updated_at IS NULL")


def downgrade() -> None:
    """Remove max_uses, uses_count, is_active, and updated_at columns from invitation_codes table."""
    # Check if columns exist before dropping
    conn = op.get_bind()
    
    # Drop is_active
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'is_active'
        )
    """))
    if result.scalar():
        op.drop_column('invitation_codes', 'is_active')
    
    # Drop uses_count
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'uses_count'
        )
    """))
    if result.scalar():
        op.drop_column('invitation_codes', 'uses_count')
    
    # Drop max_uses
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'max_uses'
        )
    """))
    if result.scalar():
        op.drop_column('invitation_codes', 'max_uses')
    
    # Drop updated_at (only if it was added by this migration)
    # Note: updated_at might have been added by another migration, so be careful
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'invitation_codes' 
            AND column_name = 'updated_at'
        )
    """))
    if result.scalar():
        op.drop_column('invitation_codes', 'updated_at')
