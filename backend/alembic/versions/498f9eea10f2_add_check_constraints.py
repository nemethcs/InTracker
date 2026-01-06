"""add_check_constraints

Revision ID: 498f9eea10f2
Revises: 8be276c52a41
Create Date: 2026-01-06 09:03:37.810834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '498f9eea10f2'
down_revision: Union[str, Sequence[str], None] = '8be276c52a41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add check constraints for status and role fields."""
    
    # Projects status constraint
    op.create_check_constraint(
        'ck_projects_status',
        'projects',
        "status IN ('active', 'paused', 'blocked', 'completed', 'archived')"
    )
    
    # Features status constraint
    op.create_check_constraint(
        'ck_features_status',
        'features',
        "status IN ('todo', 'in_progress', 'blocked', 'done')"
    )
    
    # Todos status constraint
    op.create_check_constraint(
        'ck_todos_status',
        'todos',
        "status IN ('todo', 'in_progress', 'blocked', 'done')"
    )
    
    # Project Elements status constraint
    op.create_check_constraint(
        'ck_project_elements_status',
        'project_elements',
        "status IN ('todo', 'in_progress', 'blocked', 'done')"
    )
    
    # Project Elements type constraint
    op.create_check_constraint(
        'ck_project_elements_type',
        'project_elements',
        "type IN ('module', 'feature', 'component', 'milestone', 'technical_block', 'decision_point')"
    )
    
    # User Projects role constraint
    op.create_check_constraint(
        'ck_user_projects_role',
        'user_projects',
        "role IN ('owner', 'editor', 'viewer')"
    )
    
    # Ideas status constraint
    op.create_check_constraint(
        'ck_ideas_status',
        'ideas',
        "status IN ('draft', 'active', 'archived')"
    )
    
    # Element Dependencies dependency_type constraint
    op.create_check_constraint(
        'ck_element_dependencies_type',
        'element_dependencies',
        "dependency_type IN ('blocks', 'requires', 'related')"
    )
    
    # Documents type constraint
    op.create_check_constraint(
        'ck_documents_type',
        'documents',
        "type IN ('architecture', 'adr', 'domain', 'constraints', 'runbook', 'ai_instructions')"
    )
    
    # GitHub Branches status constraint
    op.create_check_constraint(
        'ck_github_branches_status',
        'github_branches',
        "status IN ('active', 'merged', 'deleted')"
    )
    
    # GitHub Sync entity_type constraint
    op.create_check_constraint(
        'ck_github_sync_entity_type',
        'github_sync',
        "entity_type IN ('element', 'todo', 'feature', 'branch')"
    )
    
    # GitHub Sync github_type constraint
    op.create_check_constraint(
        'ck_github_sync_github_type',
        'github_sync',
        "github_type IN ('issue', 'pr', 'branch', 'commit')"
    )
    
    # GitHub Sync sync_direction constraint
    op.create_check_constraint(
        'ck_github_sync_direction',
        'github_sync',
        "sync_direction IN ('tracker_to_github', 'github_to_tracker', 'bidirectional')"
    )


def downgrade() -> None:
    """Downgrade schema - Remove check constraints."""
    op.drop_constraint('ck_projects_status', 'projects', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_project_elements_status', 'project_elements', type_='check')
    op.drop_constraint('ck_project_elements_type', 'project_elements', type_='check')
    op.drop_constraint('ck_user_projects_role', 'user_projects', type_='check')
    op.drop_constraint('ck_ideas_status', 'ideas', type_='check')
    op.drop_constraint('ck_element_dependencies_type', 'element_dependencies', type_='check')
    op.drop_constraint('ck_documents_type', 'documents', type_='check')
    op.drop_constraint('ck_github_branches_status', 'github_branches', type_='check')
    op.drop_constraint('ck_github_sync_entity_type', 'github_sync', type_='check')
    op.drop_constraint('ck_github_sync_github_type', 'github_sync', type_='check')
    op.drop_constraint('ck_github_sync_direction', 'github_sync', type_='check')
