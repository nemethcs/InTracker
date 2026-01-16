"""Unit tests for ProjectService."""
import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.services.project_service import ProjectService
from src.database.models import Project, Team, TeamMember, User


class TestProjectService:
    """Test cases for ProjectService."""
    
    def test_create_project(self, db: Session, test_team: Team, test_user: User):
        """Test creating a project."""
        # Note: create_project uses current_user_id parameter, but controller passes user_id
        # Check the actual method signature
        project = ProjectService.create_project(
            db=db,
            team_id=test_team.id,
            name="New Project",
            description="Test description",
            status="active",
            tags=["test"],
            technology_tags=["python"],
            current_user_id=test_user.id,
        )
        
        assert project is not None
        assert project.name == "New Project"
        assert project.team_id == test_team.id
        assert project.created_by == test_user.id
        assert project.updated_by == test_user.id
        
        # Verify default element was created
        from src.database.models import ProjectElement
        default_element = db.query(ProjectElement).filter(
            ProjectElement.project_id == project.id,
            ProjectElement.title == "Default"
        ).first()
        assert default_element is not None
    
    def test_get_project_by_id(self, db: Session, test_project: Project):
        """Test getting project by ID."""
        project = ProjectService.get_project_by_id(db, test_project.id)
        
        assert project is not None
        assert project.id == test_project.id
        assert project.name == test_project.name
    
    def test_get_project_by_id_not_found(self, db: Session):
        """Test getting non-existent project."""
        fake_id = uuid4()
        project = ProjectService.get_project_by_id(db, fake_id)
        
        assert project is None
    
    def test_get_user_projects(self, db: Session, test_user: User, test_team: Team, test_project: Project):
        """Test getting user projects."""
        # Add user to team
        team_member = TeamMember(
            team_id=test_team.id,
            user_id=test_user.id,
            role="member",
        )
        db.add(team_member)
        db.commit()
        
        projects, total = ProjectService.get_user_projects(
            db=db,
            user_id=test_user.id,
        )
        
        assert total >= 1
        assert any(p.id == test_project.id for p in projects)
    
    def test_get_user_projects_admin(self, db: Session, test_admin_user: User, test_project: Project):
        """Test admin user sees all projects."""
        projects, total = ProjectService.get_user_projects(
            db=db,
            user_id=test_admin_user.id,
        )
        
        assert total >= 1
        assert any(p.id == test_project.id for p in projects)
    
    def test_update_project(self, db: Session, test_project: Project, test_user: User):
        """Test updating a project."""
        updated = ProjectService.update_project(
            db=db,
            project_id=test_project.id,
            name="Updated Name",
            description="Updated description",
            current_user_id=test_user.id,
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.updated_by == test_user.id
    
    def test_delete_project(self, db: Session, test_project: Project):
        """Test deleting a project."""
        project_id = test_project.id
        result = ProjectService.delete_project(db, project_id)
        
        assert result is True
        
        # Verify project is deleted
        deleted = ProjectService.get_project_by_id(db, project_id)
        assert deleted is None
    
    def test_check_user_access_admin(self, db: Session, test_admin_user: User, test_project: Project):
        """Test admin has access to all projects."""
        has_access = ProjectService.check_user_access(
            db=db,
            user_id=test_admin_user.id,
            project_id=test_project.id,
        )
        
        assert has_access is True
    
    def test_check_user_access_team_member(self, db: Session, test_user: User, test_team: Team, test_project: Project):
        """Test team member has access to team projects."""
        # Add user to team
        team_member = TeamMember(
            team_id=test_team.id,
            user_id=test_user.id,
            role="member",
        )
        db.add(team_member)
        db.commit()
        
        has_access = ProjectService.check_user_access(
            db=db,
            user_id=test_user.id,
            project_id=test_project.id,
        )
        
        assert has_access is True
    
    def test_check_user_access_no_access(self, db: Session, test_user: User, test_project: Project):
        """Test user without team access has no access."""
        has_access = ProjectService.check_user_access(
            db=db,
            user_id=test_user.id,
            project_id=test_project.id,
        )
        
        assert has_access is False
