"""add_team_id_to_projects_and_ideas

Revision ID: d1e2f3a4b5c6
Revises: 9c2737554492
Create Date: 2026-01-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = '9c2737554492'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add team_id to projects as nullable first
    op.add_column('projects', sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('idx_projects_team', 'projects', ['team_id'], unique=False)
    
    # Step 2: Add team_id to ideas as nullable first
    op.add_column('ideas', sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('idx_ideas_team', 'ideas', ['team_id'], unique=False)
    
    # Step 3: Migrate existing data
    # For each project: assign to user's first team, or create default team
    op.execute("""
        DO $$
        DECLARE
            project_record RECORD;
            user_team_id UUID;
            default_team_id UUID;
            admin_user_id UUID;
        BEGIN
            -- Migrate projects with owners
            FOR project_record IN 
                SELECT DISTINCT ON (p.id) p.id, up.user_id
                FROM projects p
                JOIN user_projects up ON p.id = up.project_id
                WHERE up.role = 'owner'
                ORDER BY p.id, p.created_at
            LOOP
                -- Get user's first team
                SELECT tm.team_id INTO user_team_id
                FROM team_members tm
                WHERE tm.user_id = project_record.user_id
                ORDER BY tm.joined_at ASC
                LIMIT 1;
                
                -- If user has no team, create a default team
                IF user_team_id IS NULL THEN
                    -- Create default team for user
                    INSERT INTO teams (id, name, description, created_by, created_at, updated_at)
                    VALUES (
                        gen_random_uuid(),
                        'Default Team',
                        'Default team created during migration',
                        project_record.user_id,
                        NOW(),
                        NOW()
                    )
                    RETURNING id INTO default_team_id;
                    
                    -- Add user as team leader
                    INSERT INTO team_members (id, team_id, user_id, role, joined_at)
                    VALUES (
                        gen_random_uuid(),
                        default_team_id,
                        project_record.user_id,
                        'team_leader',
                        NOW()
                    );
                    
                    user_team_id := default_team_id;
                END IF;
                
                -- Assign project to team
                UPDATE projects
                SET team_id = user_team_id
                WHERE id = project_record.id;
            END LOOP;
            
            -- Handle projects without owners (assign to first available team or create default)
            FOR project_record IN 
                SELECT p.id
                FROM projects p
                WHERE p.team_id IS NULL
            LOOP
                -- Get first available team
                SELECT id INTO user_team_id
                FROM teams
                ORDER BY created_at ASC
                LIMIT 1;
                
                -- If no teams exist, create a default admin team
                IF user_team_id IS NULL THEN
                    -- Get first admin user
                    SELECT id INTO admin_user_id
                    FROM users
                    WHERE role = 'admin'
                    ORDER BY created_at ASC
                    LIMIT 1;
                    
                    IF admin_user_id IS NOT NULL THEN
                        INSERT INTO teams (id, name, description, created_by, created_at, updated_at)
                        VALUES (
                            gen_random_uuid(),
                            'Admin Default Team',
                            'Default team for admin users',
                            admin_user_id,
                            NOW(),
                            NOW()
                        )
                        RETURNING id INTO default_team_id;
                        
                        user_team_id := default_team_id;
                    END IF;
                END IF;
                
                IF user_team_id IS NOT NULL THEN
                    UPDATE projects
                    SET team_id = user_team_id
                    WHERE id = project_record.id;
                END IF;
            END LOOP;
        END $$;
    """)
    
    # Step 4: Migrate existing ideas
    # For each idea: assign to first available team, or create default team
    op.execute("""
        DO $$
        DECLARE
            idea_record RECORD;
            user_team_id UUID;
            default_team_id UUID;
            admin_user_id UUID;
        BEGIN
            FOR idea_record IN 
                SELECT i.id, i.created_at
                FROM ideas i
                WHERE i.team_id IS NULL
                ORDER BY i.created_at
            LOOP
                -- Get first available team
                SELECT id INTO user_team_id
                FROM teams
                ORDER BY created_at ASC
                LIMIT 1;
                
                -- If no teams exist, create a default team
                IF user_team_id IS NULL THEN
                    -- Get first admin user
                    SELECT id INTO admin_user_id
                    FROM users
                    WHERE role = 'admin'
                    ORDER BY created_at ASC
                    LIMIT 1;
                    
                    IF admin_user_id IS NOT NULL THEN
                        INSERT INTO teams (id, name, description, created_by, created_at, updated_at)
                        VALUES (
                            gen_random_uuid(),
                            'Admin Default Team',
                            'Default team for admin users',
                            admin_user_id,
                            NOW(),
                            NOW()
                        )
                        RETURNING id INTO default_team_id;
                        
                        user_team_id := default_team_id;
                    END IF;
                END IF;
                
                IF user_team_id IS NOT NULL THEN
                    UPDATE ideas
                    SET team_id = user_team_id
                    WHERE id = idea_record.id;
                END IF;
            END LOOP;
        END $$;
    """)
    
    # Step 5: Add foreign key constraints
    op.create_foreign_key(
        'fk_projects_team_id',
        'projects', 'teams',
        ['team_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_ideas_team_id',
        'ideas', 'teams',
        ['team_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Step 6: Make team_id non-nullable
    op.alter_column('projects', 'team_id', nullable=False)
    op.alter_column('ideas', 'team_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key constraints
    op.drop_constraint('fk_ideas_team_id', 'ideas', type_='foreignkey')
    op.drop_constraint('fk_projects_team_id', 'projects', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_ideas_team', table_name='ideas')
    op.drop_index('idx_projects_team', table_name='projects')
    
    # Drop columns
    op.drop_column('ideas', 'team_id')
    op.drop_column('projects', 'team_id')
