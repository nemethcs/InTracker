"""Pytest configuration and fixtures."""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from uuid import UUID
from typing import Generator

from src.database.base import Base, get_db
from src.database.models import User, Team, Project, ProjectElement, Feature, Todo
from src.config import settings


# Use the same database as production, but with transaction rollback for test isolation
# This ensures tests use the same schema as production
from src.database.base import get_database_url, engine

# Use the production database engine, but create a separate session factory for tests
# Tests will use transaction rollback to isolate changes
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a test database session with transaction rollback for isolation.
    
    Uses the production database but rolls back all changes after each test.
    This ensures tests don't affect each other or production data.
    """
    # Create session
    session = TestingSessionLocal()
    
    # Start a nested transaction (savepoint)
    # This allows us to rollback all changes made during the test
    trans = session.begin_nested()
    
    try:
        yield session
    finally:
        # Rollback the nested transaction to undo all changes
        trans.rollback()
        session.close()


@pytest.fixture
def override_get_db(db: Session):
    """Override get_db dependency for testing."""
    def _get_db():
        try:
            yield db
        finally:
            pass  # Don't close in tests, handled by fixture
    
    return _get_db


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user with unique email."""
    import uuid
    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        name="Test User",
        password_hash="hashed_password",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db: Session) -> User:
    """Create a test admin user with unique email."""
    import uuid
    unique_email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        name="Admin User",
        password_hash="hashed_password",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(user)
    return user


@pytest.fixture
def test_team(db: Session, test_user: User) -> Team:
    """Create a test team with unique name."""
    import uuid
    unique_name = f"Test Team {uuid.uuid4().hex[:8]}"
    team = Team(
        name=unique_name,
        description="Test team description",
        language="en",
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db.add(team)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(team)
    return team


@pytest.fixture
def test_project(db: Session, test_team: Team, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        name="Test Project",
        description="Test project description",
        status="active",
        team_id=test_team.id,
        tags=["test"],
        technology_tags=["python", "fastapi"],
    )
    db.add(project)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(project)
    return project


@pytest.fixture
def test_element(db: Session, test_project: Project) -> ProjectElement:
    """Create a test element."""
    element = ProjectElement(
        project_id=test_project.id,
        type="module",
        title="Test Element",
        description="Test element description",
        status="new",
    )
    db.add(element)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(element)
    return element


@pytest.fixture
def test_feature(db: Session, test_project: Project) -> Feature:
    """Create a test feature."""
    feature = Feature(
        project_id=test_project.id,
        name="Test Feature",
        description="Test feature description",
        status="new",
        total_todos=0,
        completed_todos=0,
        progress_percentage=0,
    )
    db.add(feature)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(feature)
    return feature


@pytest.fixture
def test_todo(db: Session, test_element: ProjectElement, test_feature: Feature) -> Todo:
    """Create a test todo."""
    todo = Todo(
        element_id=test_element.id,
        feature_id=test_feature.id,
        title="Test Todo",
        description="Test todo description",
        status="new",
        priority="medium",
        version=1,
    )
    db.add(todo)
    db.flush()  # Use flush instead of commit to keep transaction open
    db.refresh(todo)
    return todo
