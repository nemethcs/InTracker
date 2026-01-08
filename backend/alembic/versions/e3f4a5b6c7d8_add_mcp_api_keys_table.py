"""add_mcp_api_keys_table

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c6
Create Date: 2026-01-08 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create mcp_api_keys table."""
    op.create_table(
        'mcp_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_mcp_api_keys_user', 'mcp_api_keys', ['user_id'], unique=False)
    op.create_index('idx_mcp_api_keys_active', 'mcp_api_keys', ['is_active'], unique=False)
    op.create_index('idx_mcp_api_keys_key_hash', 'mcp_api_keys', ['key_hash'], unique=True)


def downgrade() -> None:
    """Downgrade schema - drop mcp_api_keys table."""
    op.drop_index('idx_mcp_api_keys_key_hash', table_name='mcp_api_keys')
    op.drop_index('idx_mcp_api_keys_active', table_name='mcp_api_keys')
    op.drop_index('idx_mcp_api_keys_user', table_name='mcp_api_keys')
    op.drop_table('mcp_api_keys')
