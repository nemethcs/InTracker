"""add_github_oauth_token_fields_to_users

Revision ID: dfcfe59b50e6
Revises: dbb1c0220ee1
Create Date: 2026-01-12 13:19:00.042075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfcfe59b50e6'
down_revision: Union[str, Sequence[str], None] = 'dbb1c0220ee1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add GitHub OAuth token fields to users table (idempotent)."""
    conn = op.get_bind()
    
    # Check if github_access_token_encrypted column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_access_token_encrypted'
        )
    """))
    access_token_exists = result.scalar()
    
    if not access_token_exists:
        op.add_column('users', 
            sa.Column('github_access_token_encrypted', sa.Text(), nullable=True)
        )
    
    # Check if github_refresh_token_encrypted column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_refresh_token_encrypted'
        )
    """))
    refresh_token_exists = result.scalar()
    
    if not refresh_token_exists:
        op.add_column('users', 
            sa.Column('github_refresh_token_encrypted', sa.Text(), nullable=True)
        )
    
    # Check if github_token_expires_at column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_token_expires_at'
        )
    """))
    expires_at_exists = result.scalar()
    
    if not expires_at_exists:
        op.add_column('users', 
            sa.Column('github_token_expires_at', sa.DateTime(), nullable=True)
        )
    
    # Check if github_refresh_token_expires_at column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_refresh_token_expires_at'
        )
    """))
    refresh_expires_at_exists = result.scalar()
    
    if not refresh_expires_at_exists:
        op.add_column('users', 
            sa.Column('github_refresh_token_expires_at', sa.DateTime(), nullable=True)
        )
    
    # Check if github_connected_at column exists
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_connected_at'
        )
    """))
    connected_at_exists = result.scalar()
    
    if not connected_at_exists:
        op.add_column('users', 
            sa.Column('github_connected_at', sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    """Remove GitHub OAuth token fields from users table (idempotent)."""
    conn = op.get_bind()
    
    # Check if github_connected_at column exists and remove it
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_connected_at'
        )
    """))
    if result.scalar():
        op.drop_column('users', 'github_connected_at')
    
    # Check if github_refresh_token_expires_at column exists and remove it
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_refresh_token_expires_at'
        )
    """))
    if result.scalar():
        op.drop_column('users', 'github_refresh_token_expires_at')
    
    # Check if github_token_expires_at column exists and remove it
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_token_expires_at'
        )
    """))
    if result.scalar():
        op.drop_column('users', 'github_token_expires_at')
    
    # Check if github_refresh_token_encrypted column exists and remove it
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_refresh_token_encrypted'
        )
    """))
    if result.scalar():
        op.drop_column('users', 'github_refresh_token_encrypted')
    
    # Check if github_access_token_encrypted column exists and remove it
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'github_access_token_encrypted'
        )
    """))
    if result.scalar():
        op.drop_column('users', 'github_access_token_encrypted')
