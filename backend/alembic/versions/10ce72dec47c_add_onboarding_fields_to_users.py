"""add_onboarding_fields_to_users

Revision ID: 10ce72dec47c
Revises: dfcfe59b50e6
Create Date: 2026-01-13 15:38:25.009990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10ce72dec47c'
down_revision: Union[str, Sequence[str], None] = 'dfcfe59b50e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    
    # Add onboarding_step
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'onboarding_step')"))
    if not result.scalar():
        op.add_column('users', sa.Column('onboarding_step', sa.Integer(), nullable=False, server_default='0'))
    
    # Add mcp_verified_at
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'mcp_verified_at')"))
    if not result.scalar():
        op.add_column('users', sa.Column('mcp_verified_at', sa.DateTime(), nullable=True))
    
    # Add setup_completed
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'setup_completed')"))
    if not result.scalar():
        op.add_column('users', sa.Column('setup_completed', sa.Boolean(), nullable=False, server_default='false'))
    
    # Set setup_completed = true for existing users who have both MCP key and GitHub connected
    # This is a one-time data migration for existing users
    conn.execute(sa.text("""
        UPDATE users
        SET setup_completed = true
        WHERE id IN (
            SELECT DISTINCT u.id
            FROM users u
            WHERE EXISTS (
                SELECT 1 FROM mcp_api_keys m
                WHERE m.user_id = u.id AND m.is_active = true
            )
            AND u.github_access_token_encrypted IS NOT NULL
        )
    """))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'setup_completed')"))
    if result.scalar():
        op.drop_column('users', 'setup_completed')
    
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'mcp_verified_at')"))
    if result.scalar():
        op.drop_column('users', 'mcp_verified_at')
    
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'onboarding_step')"))
    if result.scalar():
        op.drop_column('users', 'onboarding_step')
