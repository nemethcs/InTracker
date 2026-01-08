"""move_tested_merged_from_todos_to_features

Revision ID: a2ba13b96d48
Revises: c1d2e3f4a5b6
Create Date: 2026-01-07 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2ba13b96d48'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Move tested/merged from todos to features.
    
    New workflow:
    - Todos: new → in_progress → done (simplified)
    - Features: new → in_progress → done → tested → merged (feature-level testing and merging)
    """
    
    # Drop old constraints to allow data updates
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    
    # Migrate existing data:
    # - Todos with 'tested' or 'merged' status → 'done' (they are completed)
    op.execute("UPDATE todos SET status = 'done' WHERE status IN ('tested', 'merged')")
    
    # - Features with 'done' status → 'tested' (if they have all todos done)
    #   Note: We'll mark features as 'tested' if all their todos are done
    #   This is a reasonable assumption for the migration
    op.execute("""
        UPDATE features 
        SET status = 'tested' 
        WHERE status = 'done' 
        AND total_todos > 0 
        AND completed_todos = total_todos
    """)
    
    # Create new constraints with updated status values
    # For todos: new, in_progress, done (removed tested, merged)
    op.create_check_constraint(
        'ck_todos_status',
        'todos',
        "status IN ('new', 'in_progress', 'done')"
    )
    
    # For features: new, in_progress, done, tested, merged (added tested, merged)
    op.create_check_constraint(
        'ck_features_status',
        'features',
        "status IN ('new', 'in_progress', 'done', 'tested', 'merged')"
    )


def downgrade() -> None:
    """Downgrade schema - Revert tested/merged back to todos."""
    
    # Drop new constraints
    op.drop_constraint('ck_todos_status', 'todos', type_='check')
    op.drop_constraint('ck_features_status', 'features', type_='check')
    
    # Revert data changes
    # - Features with 'tested' or 'merged' → 'done' (simplified)
    op.execute("UPDATE features SET status = 'done' WHERE status IN ('tested', 'merged')")
    
    # - Todos: keep 'done' as 'done' (we can't know which ones were tested/merged)
    #   This is a lossy migration, but necessary for downgrade
    
    # Restore old constraints
    # For todos: new, in_progress, done, tested, merged
    op.create_check_constraint(
        'ck_todos_status',
        'todos',
        "status IN ('new', 'in_progress', 'done', 'tested', 'merged')"
    )
    
    # For features: new, in_progress, done, tested (removed merged)
    op.create_check_constraint(
        'ck_features_status',
        'features',
        "status IN ('new', 'in_progress', 'done', 'tested')"
    )
