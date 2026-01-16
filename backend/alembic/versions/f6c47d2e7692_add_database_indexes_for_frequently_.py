"""add_database_indexes_for_frequently_queried_columns

Revision ID: f6c47d2e7692
Revises: 6e03cddcf00a
Create Date: 2026-01-15 17:28:20.791569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6c47d2e7692'
down_revision: Union[str, Sequence[str], None] = '6e03cddcf00a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add database indexes for frequently queried columns.
    
    This migration adds composite indexes for commonly queried column combinations
    to improve query performance, especially for filtered and sorted queries.
    """
    # Session indexes
    # Frequently queried: project_id + user_id together
    op.create_index(
        'idx_sessions_project_user',
        'sessions',
        ['project_id', 'user_id'],
        unique=False
    )
    # Frequently queried: project_id + started_at for ORDER BY started_at DESC
    op.create_index(
        'idx_sessions_project_started',
        'sessions',
        ['project_id', 'started_at'],
        unique=False
    )
    
    # Document indexes
    # Frequently queried: project_id + type together
    op.create_index(
        'idx_documents_project_type',
        'documents',
        ['project_id', 'type'],
        unique=False
    )
    # Frequently queried: project_id + updated_at for ORDER BY updated_at DESC
    op.create_index(
        'idx_documents_project_updated',
        'documents',
        ['project_id', 'updated_at'],
        unique=False
    )
    
    # Feature indexes
    # Frequently queried: project_id + status together
    op.create_index(
        'idx_features_project_status',
        'features',
        ['project_id', 'status'],
        unique=False
    )
    # Frequently queried: project_id + updated_at for ORDER BY updated_at DESC
    op.create_index(
        'idx_features_project_updated',
        'features',
        ['project_id', 'updated_at'],
        unique=False
    )
    
    # Todo indexes
    # Frequently queried: feature_id + status together
    op.create_index(
        'idx_todos_feature_status',
        'todos',
        ['feature_id', 'status'],
        unique=False
    )
    # Frequently queried: element_id + status together
    op.create_index(
        'idx_todos_element_status',
        'todos',
        ['element_id', 'status'],
        unique=False
    )
    
    # Project indexes
    # Frequently queried: team_id + status together
    op.create_index(
        'idx_projects_team_status',
        'projects',
        ['team_id', 'status'],
        unique=False
    )
    # Frequently queried: team_id + created_at for ORDER BY created_at DESC
    op.create_index(
        'idx_projects_team_created',
        'projects',
        ['team_id', 'created_at'],
        unique=False
    )
    
    # Idea indexes
    # Frequently queried: team_id + status together
    op.create_index(
        'idx_ideas_team_status',
        'ideas',
        ['team_id', 'status'],
        unique=False
    )
    # Frequently queried: team_id + created_at for ORDER BY created_at DESC
    op.create_index(
        'idx_ideas_team_created',
        'ideas',
        ['team_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove database indexes added in upgrade."""
    # Session indexes
    op.drop_index('idx_sessions_project_user', table_name='sessions')
    op.drop_index('idx_sessions_project_started', table_name='sessions')
    
    # Document indexes
    op.drop_index('idx_documents_project_type', table_name='documents')
    op.drop_index('idx_documents_project_updated', table_name='documents')
    
    # Feature indexes
    op.drop_index('idx_features_project_status', table_name='features')
    op.drop_index('idx_features_project_updated', table_name='features')
    
    # Todo indexes
    op.drop_index('idx_todos_feature_status', table_name='todos')
    op.drop_index('idx_todos_element_status', table_name='todos')
    
    # Project indexes
    op.drop_index('idx_projects_team_status', table_name='projects')
    op.drop_index('idx_projects_team_created', table_name='projects')
    
    # Idea indexes
    op.drop_index('idx_ideas_team_status', table_name='ideas')
    op.drop_index('idx_ideas_team_created', table_name='ideas')
