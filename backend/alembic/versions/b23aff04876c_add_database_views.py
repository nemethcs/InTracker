"""add_database_views

Revision ID: b23aff04876c
Revises: 8c6193b3b19e
Create Date: 2026-01-06 09:08:30.011573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b23aff04876c'
down_revision: Union[str, Sequence[str], None] = '8c6193b3b19e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add database views."""
    
    # User Projects View - combines users, projects, and roles
    op.execute("""
        CREATE OR REPLACE VIEW user_projects_with_roles AS
        SELECT 
            u.id AS user_id,
            u.email,
            u.name AS user_name,
            p.id AS project_id,
            p.name AS project_name,
            p.status AS project_status,
            up.role,
            up.created_at AS assigned_at
        FROM users u
        INNER JOIN user_projects up ON u.id = up.user_id
        INNER JOIN projects p ON up.project_id = p.id
        WHERE u.is_active = TRUE;
    """)
    
    # Project Statistics View
    op.execute("""
        CREATE OR REPLACE VIEW project_statistics AS
        SELECT 
            p.id AS project_id,
            p.name AS project_name,
            p.status AS project_status,
            COUNT(DISTINCT f.id) AS feature_count,
            COUNT(DISTINCT CASE WHEN f.status = 'done' THEN f.id END) AS completed_features,
            COUNT(DISTINCT t.id) AS todo_count,
            COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END) AS completed_todos,
            COUNT(DISTINCT CASE WHEN t.status IN ('todo', 'in_progress', 'blocked') THEN t.id END) AS active_todos,
            COUNT(DISTINCT pe.id) AS element_count,
            COUNT(DISTINCT s.id) AS session_count,
            CASE 
                WHEN COUNT(DISTINCT t.id) > 0 THEN 
                    ROUND((COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END)::NUMERIC / COUNT(DISTINCT t.id)::NUMERIC) * 100, 2)
                ELSE 0
            END AS completion_rate
        FROM projects p
        LEFT JOIN features f ON p.id = f.project_id
        LEFT JOIN todos t ON f.id = t.feature_id
        LEFT JOIN project_elements pe ON p.id = pe.project_id
        LEFT JOIN sessions s ON p.id = s.project_id
        GROUP BY p.id, p.name, p.status;
    """)
    
    # User Activity View
    op.execute("""
        CREATE OR REPLACE VIEW user_activity_summary AS
        SELECT 
            u.id AS user_id,
            u.email,
            u.name AS user_name,
            MAX(s.ended_at) AS last_session_at,
            COUNT(DISTINCT CASE WHEN t.status IN ('todo', 'in_progress', 'blocked') THEN t.id END) AS active_todos_count,
            COUNT(DISTINCT CASE WHEN f.status IN ('todo', 'in_progress', 'blocked') THEN f.id END) AS active_features_count,
            COUNT(DISTINCT p.id) AS project_count,
            COUNT(DISTINCT s.id) AS total_sessions
        FROM users u
        LEFT JOIN user_projects up ON u.id = up.user_id
        LEFT JOIN projects p ON up.project_id = p.id
        LEFT JOIN todos t ON (t.assigned_to = u.id OR t.created_by = u.id)
        LEFT JOIN features f ON (f.assigned_to = u.id OR f.created_by = u.id)
        LEFT JOIN sessions s ON s.user_id = u.id
        WHERE u.is_active = TRUE
        GROUP BY u.id, u.email, u.name;
    """)
    
    # Team Dashboard Materialized View (will be refreshed periodically)
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS team_dashboard_data AS
        SELECT 
            p.id AS project_id,
            p.name AS project_name,
            p.status AS project_status,
            COUNT(DISTINCT up.user_id) AS team_size,
            COUNT(DISTINCT f.id) AS total_features,
            COUNT(DISTINCT CASE WHEN f.status = 'done' THEN f.id END) AS completed_features,
            COUNT(DISTINCT t.id) AS total_todos,
            COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END) AS completed_todos,
            COUNT(DISTINCT CASE WHEN t.status = 'in_progress' THEN t.id END) AS in_progress_todos,
            COUNT(DISTINCT CASE WHEN t.status = 'blocked' THEN t.id END) AS blocked_todos,
            MAX(s.ended_at) AS last_activity_at,
            CASE 
                WHEN COUNT(DISTINCT t.id) > 0 THEN 
                    ROUND((COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END)::NUMERIC / COUNT(DISTINCT t.id)::NUMERIC) * 100, 2)
                ELSE 0
            END AS overall_completion_rate
        FROM projects p
        LEFT JOIN user_projects up ON p.id = up.project_id
        LEFT JOIN features f ON p.id = f.project_id
        LEFT JOIN todos t ON f.id = t.feature_id
        LEFT JOIN sessions s ON p.id = s.project_id
        WHERE p.status IN ('active', 'in_progress')
        GROUP BY p.id, p.name, p.status;
        
        CREATE UNIQUE INDEX ON team_dashboard_data (project_id);
    """)


def downgrade() -> None:
    """Downgrade schema - Remove database views."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS team_dashboard_data;")
    op.execute("DROP VIEW IF EXISTS user_activity_summary;")
    op.execute("DROP VIEW IF EXISTS project_statistics;")
    op.execute("DROP VIEW IF EXISTS user_projects_with_roles;")
