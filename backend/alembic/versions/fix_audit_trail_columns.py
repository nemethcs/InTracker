"""fix_audit_trail_columns

Revision ID: fix_audit_001
Revises: c888c28d3cf5
Create Date: 2026-01-09 21:00:00.000000

This migration fixes the audit trail columns by using idempotent SQL
that checks if columns exist before adding them.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_audit_001'
down_revision: Union[str, Sequence[str], None] = 'c888c28d3cf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing audit trail columns using idempotent SQL."""
    
    # Use raw SQL with IF NOT EXISTS to avoid errors
    conn = op.get_bind()
    
    # List of tables and their required audit columns
    tables_to_fix = [
        ('projects', ['created_by', 'updated_by']),
        ('features', ['updated_by']),  # created_by already exists
        ('todos', ['updated_by']),  # created_by already exists
        ('project_elements', ['created_by', 'updated_by']),
        ('documents', ['created_by', 'updated_by']),
        ('sessions', ['created_by', 'updated_by']),
        ('ideas', ['created_by', 'updated_by']),
        ('teams', ['updated_by']),  # created_by already exists
        ('invitation_codes', ['updated_by']),  # created_by already exists
        ('element_dependencies', ['created_by', 'updated_by']),
        ('github_branches', ['created_by', 'updated_by']),
        ('github_sync', ['created_by', 'updated_by']),
        ('team_members', ['created_by', 'updated_by']),
        ('mcp_api_keys', ['created_by', 'updated_by']),
    ]
    
    for table_name, columns in tables_to_fix:
        for column_name in columns:
            # Check if column exists, if not add it
            conn.execute(sa.text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{column_name}'
                    ) THEN
                        ALTER TABLE {table_name} ADD COLUMN {column_name} UUID;
                    END IF;
                END $$;
            """))
            
            # Check if foreign key exists, if not add it
            fk_name = f"fk_{table_name}_{column_name}_users"
            conn.execute(sa.text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = '{fk_name}'
                        AND table_name = '{table_name}'
                    ) THEN
                        ALTER TABLE {table_name} 
                        ADD CONSTRAINT {fk_name} 
                        FOREIGN KEY ({column_name}) REFERENCES users(id);
                    END IF;
                END $$;
            """))
            
            # Check if index exists, if not add it
            idx_name = f"idx_{table_name}_{column_name}"
            conn.execute(sa.text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = '{idx_name}'
                    ) THEN
                        CREATE INDEX {idx_name} ON {table_name} ({column_name});
                    END IF;
                END $$;
            """))


def downgrade() -> None:
    """This migration is idempotent and doesn't need a downgrade."""
    pass
