"""replace_estimated_effort_with_priority

Revision ID: b373fdc81e8c
Revises: b23aff04876c
Create Date: 2026-01-06 14:35:03.107012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b373fdc81e8c'
down_revision: Union[str, Sequence[str], None] = 'b23aff04876c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop estimated_effort column
    op.drop_column('todos', 'estimated_effort')
    
    # Add priority column with default value
    op.add_column('todos', sa.Column('priority', sa.String(), nullable=True, server_default='medium'))
    
    # Add check constraint for priority values
    op.create_check_constraint(
        'ck_todos_priority',
        'todos',
        "priority IN ('low', 'medium', 'high', 'critical') OR priority IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove check constraint
    op.drop_constraint('ck_todos_priority', 'todos', type_='check')
    
    # Drop priority column
    op.drop_column('todos', 'priority')
    
    # Add back estimated_effort column
    op.add_column('todos', sa.Column('estimated_effort', sa.Integer(), nullable=True))
