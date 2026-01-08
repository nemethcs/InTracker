"""update_todo_status_workflow_to_new_format

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-07 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Update todo status workflow: new → in_progress → done → tested → merged."""
    
    # Drop old constraints to allow data updates
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_project_elements_status', 'project_elements', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    
    # Update existing data:
    # - 'tested' todos should become 'done' (they were tested but not merged yet)
    # - 'done' todos should become 'merged' (they were done and merged)
    # Note: This is a logical mapping based on the new workflow
    op.execute("UPDATE todos SET status = 'done' WHERE status = 'tested'")
    op.execute("UPDATE todos SET status = 'merged' WHERE status = 'done'")
    
    # For project_elements and features, we'll keep the same mapping
    # but note that 'merged' doesn't apply to them, so we'll map:
    # - 'tested' -> 'done' (completed and tested)
    # - 'done' -> 'done' (already done)
    op.execute("UPDATE project_elements SET status = 'done' WHERE status = 'tested'")
    # Keep 'done' as 'done' for elements and features
    
    op.execute("UPDATE features SET status = 'done' WHERE status = 'tested'")
    # Keep 'done' as 'done' for features
    
    # Create new constraints with new status values
    # For todos: new, in_progress, done, tested, merged
    op.create_check_constraint(
        'ck_todos_status',
        'todos',
        "status IN ('new', 'in_progress', 'done', 'tested', 'merged')"
    )
    
    # For project_elements and features: new, in_progress, done, tested
    # (merged doesn't apply to elements/features)
    op.create_check_constraint(
        'ck_project_elements_status',
        'project_elements',
        "status IN ('new', 'in_progress', 'done', 'tested')"
    )
    
    op.create_check_constraint(
        'ck_features_status',
        'features',
        "status IN ('new', 'in_progress', 'done', 'tested')"
    )


def downgrade() -> None:
    """Downgrade schema - Revert to old status workflow: new → in_progress → tested → done."""
    
    # Drop new constraints
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_project_elements_status', 'project_elements', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    
    # Revert data changes
    # For todos:
    # - 'merged' -> 'done' (was done and merged, now just done)
    # - 'done' -> 'tested' (was done, now tested)
    # - 'tested' -> 'tested' (was tested, stays tested)
    op.execute("UPDATE todos SET status = 'done' WHERE status = 'merged'")
    op.execute("UPDATE todos SET status = 'tested' WHERE status = 'done'")
    
    # For project_elements and features:
    # - 'done' -> 'tested' (was done, now tested)
    op.execute("UPDATE project_elements SET status = 'tested' WHERE status = 'done'")
    op.execute("UPDATE features SET status = 'tested' WHERE status = 'done'")
    
    # Restore old constraints
    op.create_check_constraint(
        'ck_todos_status',
        'todos',
        "status IN ('new', 'in_progress', 'tested', 'done')"
    )
    
    op.create_check_constraint(
        'ck_project_elements_status',
        'project_elements',
        "status IN ('new', 'in_progress', 'tested', 'done')"
    )
    
    op.create_check_constraint(
        'ck_features_status',
        'features',
        "status IN ('new', 'in_progress', 'tested', 'done')"
    )
