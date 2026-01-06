"""add_database_triggers

Revision ID: 8c6193b3b19e
Revises: 498f9eea10f2
Create Date: 2026-01-06 09:05:08.394279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c6193b3b19e'
down_revision: Union[str, Sequence[str], None] = '498f9eea10f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add database triggers and functions."""
    
    # Function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at on all tables that have it
    tables_with_updated_at = [
        'users', 'projects', 'project_elements', 'features', 'todos',
        'documents', 'sessions', 'ideas', 'github_branches', 'github_sync'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
    
    # Function to calculate feature progress
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_feature_progress(feature_uuid UUID)
        RETURNS VOID AS $$
        DECLARE
            total_count INTEGER;
            completed_count INTEGER;
            progress_pct INTEGER;
        BEGIN
            -- Count total todos for feature
            SELECT COUNT(*) INTO total_count
            FROM todos
            WHERE feature_id = feature_uuid;
            
            -- Count completed todos
            SELECT COUNT(*) INTO completed_count
            FROM todos
            WHERE feature_id = feature_uuid AND status = 'done';
            
            -- Calculate progress percentage
            IF total_count > 0 THEN
                progress_pct := (completed_count * 100) / total_count;
            ELSE
                progress_pct := 0;
            END IF;
            
            -- Update feature
            UPDATE features
            SET 
                total_todos = total_count,
                completed_todos = completed_count,
                progress_percentage = progress_pct
            WHERE id = feature_uuid;
        END;
        $$ language 'plpgsql';
    """)
    
    # Function for feature progress trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_feature_progress_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.feature_id IS NOT NULL THEN
                    PERFORM calculate_feature_progress(OLD.feature_id);
                END IF;
                RETURN OLD;
            ELSIF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                IF NEW.feature_id IS NOT NULL THEN
                    PERFORM calculate_feature_progress(NEW.feature_id);
                END IF;
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ language 'plpgsql';
    """)
    
    # Trigger: Update feature progress when todo is inserted or updated
    op.execute("""
        DROP TRIGGER IF EXISTS update_feature_progress_on_todo_insert_update ON todos;
        CREATE TRIGGER update_feature_progress_on_todo_insert_update
            AFTER INSERT OR UPDATE OF status, feature_id ON todos
            FOR EACH ROW
            WHEN (NEW.feature_id IS NOT NULL)
            EXECUTE FUNCTION update_feature_progress_trigger();
    """)
    
    # Trigger: Update feature progress when todo is deleted
    op.execute("""
        DROP TRIGGER IF EXISTS update_feature_progress_on_todo_delete ON todos;
        CREATE TRIGGER update_feature_progress_on_todo_delete
            AFTER DELETE ON todos
            FOR EACH ROW
            WHEN (OLD.feature_id IS NOT NULL)
            EXECUTE FUNCTION update_feature_progress_trigger();
    """)
    
    # Function for project last_session_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_project_last_session_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE projects
            SET last_session_at = NEW.ended_at
            WHERE id = NEW.project_id;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Trigger: Update project.last_session_at when session ends
    op.execute("""
        DROP TRIGGER IF EXISTS update_project_last_session_at ON sessions;
        CREATE TRIGGER update_project_last_session_at
            AFTER UPDATE OF ended_at ON sessions
            FOR EACH ROW
            WHEN (NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL)
            EXECUTE FUNCTION update_project_last_session_trigger();
    """)
    
    # Function for version increment trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION increment_version_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.version = OLD.version + 1;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Trigger: Increment version on todo update (optimistic locking)
    op.execute("""
        DROP TRIGGER IF EXISTS increment_todo_version ON todos;
        CREATE TRIGGER increment_todo_version
            BEFORE UPDATE ON todos
            FOR EACH ROW
            EXECUTE FUNCTION increment_version_trigger();
    """)


def downgrade() -> None:
    """Downgrade schema - Remove database triggers and functions."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_feature_progress_on_todo_insert_update ON todos;")
    op.execute("DROP TRIGGER IF EXISTS update_feature_progress_on_todo_delete ON todos;")
    op.execute("DROP TRIGGER IF EXISTS update_project_last_session_at ON sessions;")
    op.execute("DROP TRIGGER IF EXISTS increment_todo_version ON todos;")
    
    tables_with_updated_at = [
        'users', 'projects', 'project_elements', 'features', 'todos',
        'documents', 'sessions', 'ideas', 'github_branches', 'github_sync'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.execute("DROP FUNCTION IF EXISTS calculate_feature_progress(UUID);")
    op.execute("DROP FUNCTION IF EXISTS update_feature_progress_trigger();")
    op.execute("DROP FUNCTION IF EXISTS update_project_last_session_trigger();")
    op.execute("DROP FUNCTION IF EXISTS increment_version_trigger();")
