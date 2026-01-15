"""add_feature_id_to_documents

Revision ID: 6e03cddcf00a
Revises: add_email_sent_001
Create Date: 2026-01-15 08:59:58.249478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6e03cddcf00a'
down_revision: Union[str, Sequence[str], None] = 'add_email_sent_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add feature_id column to documents table."""
    # Add feature_id column
    op.add_column('documents', sa.Column('feature_id', sa.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_documents_feature_id',
        'documents',
        'features',
        ['feature_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for feature_id
    op.create_index('idx_documents_feature', 'documents', ['feature_id'])


def downgrade() -> None:
    """Remove feature_id column from documents table."""
    # Drop index
    op.drop_index('idx_documents_feature', table_name='documents')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_documents_feature_id', 'documents', type_='foreignkey')
    
    # Drop column
    op.drop_column('documents', 'feature_id')
