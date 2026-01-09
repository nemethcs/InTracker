"""add_updated_by_to_all_models

Revision ID: c888c28d3cf5
Revises: 5f02dca46f48
Create Date: 2026-01-09 14:34:25.607609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c888c28d3cf5'
down_revision: Union[str, Sequence[str], None] = '5f02dca46f48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add created_by and updated_by fields to all models for audit trail."""
    from sqlalchemy.dialects.postgresql import UUID
    
    # Projects: Add created_by and updated_by
    op.add_column('projects', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('projects', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_projects_created_by', 'projects', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_projects_updated_by', 'projects', 'users', ['updated_by'], ['id'])
    op.create_index('idx_projects_created_by', 'projects', ['created_by'], unique=False)
    
    # ProjectElements: Add created_by and updated_by
    op.add_column('project_elements', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('project_elements', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_project_elements_created_by', 'project_elements', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_project_elements_updated_by', 'project_elements', 'users', ['updated_by'], ['id'])
    
    # Features: Add updated_by (created_by already exists)
    op.add_column('features', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_features_updated_by', 'features', 'users', ['updated_by'], ['id'])
    
    # Todos: Add updated_by (created_by already exists)
    op.add_column('todos', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_todos_updated_by', 'todos', 'users', ['updated_by'], ['id'])
    
    # Documents: Add created_by and updated_by
    op.add_column('documents', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('documents', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_documents_created_by', 'documents', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_documents_updated_by', 'documents', 'users', ['updated_by'], ['id'])
    
    # Sessions: Add created_by and updated_by
    op.add_column('sessions', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('sessions', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_sessions_created_by', 'sessions', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_sessions_updated_by', 'sessions', 'users', ['updated_by'], ['id'])
    
    # Ideas: Add created_by and updated_by
    op.add_column('ideas', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ideas', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_ideas_created_by', 'ideas', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_ideas_updated_by', 'ideas', 'users', ['updated_by'], ['id'])
    
    # Teams: Add updated_by (created_by already exists)
    op.add_column('teams', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_teams_updated_by', 'teams', 'users', ['updated_by'], ['id'])
    
    # InvitationCodes: Add updated_by (created_by already exists)
    op.add_column('invitation_codes', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_invitation_codes_updated_by', 'invitation_codes', 'users', ['updated_by'], ['id'])


def downgrade() -> None:
    """Downgrade schema - Remove created_by and updated_by fields."""
    # Remove foreign keys and columns in reverse order
    op.drop_constraint('fk_invitation_codes_updated_by', 'invitation_codes', type_='foreignkey')
    op.drop_column('invitation_codes', 'updated_by')
    
    op.drop_constraint('fk_teams_updated_by', 'teams', type_='foreignkey')
    op.drop_column('teams', 'updated_by')
    
    op.drop_constraint('fk_ideas_updated_by', 'ideas', type_='foreignkey')
    op.drop_constraint('fk_ideas_created_by', 'ideas', type_='foreignkey')
    op.drop_column('ideas', 'updated_by')
    op.drop_column('ideas', 'created_by')
    
    op.drop_constraint('fk_sessions_updated_by', 'sessions', type_='foreignkey')
    op.drop_constraint('fk_sessions_created_by', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'updated_by')
    op.drop_column('sessions', 'created_by')
    
    op.drop_constraint('fk_documents_updated_by', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_created_by', 'documents', type_='foreignkey')
    op.drop_column('documents', 'updated_by')
    op.drop_column('documents', 'created_by')
    
    op.drop_constraint('fk_todos_updated_by', 'todos', type_='foreignkey')
    op.drop_column('todos', 'updated_by')
    
    op.drop_constraint('fk_features_updated_by', 'features', type_='foreignkey')
    op.drop_column('features', 'updated_by')
    
    op.drop_constraint('fk_project_elements_updated_by', 'project_elements', type_='foreignkey')
    op.drop_constraint('fk_project_elements_created_by', 'project_elements', type_='foreignkey')
    op.drop_column('project_elements', 'updated_by')
    op.drop_column('project_elements', 'created_by')
    
    op.drop_index('idx_projects_created_by', table_name='projects')
    op.drop_constraint('fk_projects_updated_by', 'projects', type_='foreignkey')
    op.drop_constraint('fk_projects_created_by', 'projects', type_='foreignkey')
    op.drop_column('projects', 'updated_by')
    op.drop_column('projects', 'created_by')
