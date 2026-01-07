"""update_todo_statuses_to_rules_format

Revision ID: a1b2c3d4e5f6
Revises: 498f9eea10f2
Create Date: 2026-01-06 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b373fdc81e8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Update todo statuses to match rules: new, in_progress, tested, done."""
    
    # First, drop old constraints to allow data updates
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_project_elements_status', 'project_elements', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    
    # Now update existing data
    # todo -> new
    op.execute("UPDATE todos SET status = 'new' WHERE status = 'todo'")
    # blocked -> in_progress (temporary, then we'll handle blocked separately)
    # Actually, we should remove blocked status - convert to in_progress for now
    op.execute("UPDATE todos SET status = 'in_progress' WHERE status = 'blocked'")
    
    # Update Project Elements statuses too
    op.execute("UPDATE project_elements SET status = 'new' WHERE status = 'todo'")
    op.execute("UPDATE project_elements SET status = 'in_progress' WHERE status = 'blocked'")
    
    # Update Features statuses too
    op.execute("UPDATE features SET status = 'new' WHERE status = 'todo'")
    op.execute("UPDATE features SET status = 'in_progress' WHERE status = 'blocked'")
    
    # Create new constraints with new status values
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


def downgrade() -> None:
    """Downgrade schema - Revert to old status values."""
    
    # Drop new constraints
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_project_elements_status', 'project_elements', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    
    # Revert data changes
    # new -> todo
    op.execute("UPDATE todos SET status = 'todo' WHERE status = 'new'")
    op.execute("UPDATE project_elements SET status = 'todo' WHERE status = 'new'")
    op.execute("UPDATE features SET status = 'todo' WHERE status = 'new'")
    
    # tested -> done (best approximation)
    op.execute("UPDATE todos SET status = 'done' WHERE status = 'tested'")
    op.execute("UPDATE project_elements SET status = 'done' WHERE status = 'tested'")
    op.execute("UPDATE features SET status = 'done' WHERE status = 'tested'")
    
    # Restore old constraints
    op.create_check_constraint(
        'ck_todos_status',
        'todos',
        "status IN ('todo', 'in_progress', 'blocked', 'done')"
    )
    
    op.create_check_constraint(
        'ck_project_elements_status',
        'project_elements',
        "status IN ('todo', 'in_progress', 'blocked', 'done')"
    )
    
    op.create_check_constraint(
        'ck_features_status',
        'features',
        "status IN ('todo', 'in_progress', 'blocked', 'done')"
    )
