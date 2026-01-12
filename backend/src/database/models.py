"""SQLAlchemy models matching Prisma schema."""
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    Text,
    ForeignKey,
    ARRAY,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.base import Base
import uuid


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="member", nullable=False, index=True)  # admin, team_leader, member
    github_username = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    # GitHub OAuth tokens (encrypted)
    github_access_token_encrypted = Column(Text, nullable=True)  # Encrypted access token
    github_refresh_token_encrypted = Column(Text, nullable=True)  # Encrypted refresh token
    github_token_expires_at = Column(DateTime, nullable=True)  # Access token expiration time
    github_refresh_token_expires_at = Column(DateTime, nullable=True)  # Refresh token expiration time
    github_connected_at = Column(DateTime, nullable=True)  # When OAuth connection was established
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # user_projects relationship removed - projects are now team-based
    created_todos = relationship("Todo", foreign_keys="Todo.created_by", back_populates="creator")
    assigned_todos = relationship("Todo", foreign_keys="Todo.assigned_to", back_populates="assigned_user")
    created_features = relationship("Feature", foreign_keys="Feature.created_by", back_populates="creator")
    assigned_features = relationship("Feature", foreign_keys="Feature.assigned_to", back_populates="assigned_user")
    sessions = relationship("Session", foreign_keys="Session.user_id", back_populates="user")
    team_memberships = relationship("TeamMember", foreign_keys="TeamMember.user_id", back_populates="user")
    created_teams = relationship("Team", foreign_keys="Team.created_by", back_populates="creator")
    created_invitations = relationship("InvitationCode", foreign_keys="InvitationCode.created_by", back_populates="creator")
    mcp_api_keys = relationship("McpApiKey", back_populates="user")


class Project(Base):
    """Project model."""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # active, paused, blocked, completed, archived
    tags = Column(ARRAY(String), default=[])
    technology_tags = Column(ARRAY(String), default=[])
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)  # Team that owns this project
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_session_at = Column(DateTime, nullable=True)
    resume_context = Column(JSON, nullable=True)
    cursor_instructions = Column(Text, nullable=True)
    github_repo_url = Column(String, nullable=True)
    github_repo_id = Column(String, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="projects")
    # user_projects relationship removed - projects are now team-based
    elements = relationship("ProjectElement", back_populates="project", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")
    ideas = relationship("Idea", back_populates="converted_to_project")
    github_branches = relationship("GitHubBranch", back_populates="project", cascade="all, delete-orphan")
    github_syncs = relationship("GitHubSync", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_team", "team_id"),
    )


# DEPRECATED: UserProject model - projects are now team-based
# This model is kept for backward compatibility but should not be used.
# The table will be removed in a future migration.
# class UserProject(Base):
#     """User-Project relationship model (DEPRECATED)."""
#     __tablename__ = "user_projects"
#
#     user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
#     project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
#     role = Column(String, nullable=False)  # owner, editor, viewer
#     created_at = Column(DateTime, server_default=func.now(), nullable=False)
#
#     # Relationships
#     user = relationship("User", back_populates="user_projects")
#     project = relationship("Project", back_populates="user_projects")
#
#     __table_args__ = (
#         Index("idx_user_projects_user", "user_id"),
#         Index("idx_user_projects_project", "project_id"),
#     )


class ProjectElement(Base):
    """Project Element model."""
    __tablename__ = "project_elements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("project_elements.id", ondelete="CASCADE"), nullable=True)
    type = Column(String, nullable=False)  # module, feature, component, milestone, technical_block, decision_point
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # new, in_progress, done, tested, merged
    position = Column(Integer, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    definition_of_done = Column(Text, nullable=True)
    github_issue_number = Column(Integer, nullable=True)
    github_issue_url = Column(String, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="elements")
    parent = relationship("ProjectElement", remote_side=[id], backref="children")
    todos = relationship("Todo", back_populates="element", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="element")
    feature_elements = relationship("FeatureElement", back_populates="element", cascade="all, delete-orphan")
    dependencies = relationship(
        "ElementDependency",
        foreign_keys="ElementDependency.element_id",
        back_populates="element",
        cascade="all, delete-orphan",
    )
    depends_on = relationship(
        "ElementDependency",
        foreign_keys="ElementDependency.depends_on_element_id",
        back_populates="depends_on",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_project_elements_project", "project_id"),
        Index("idx_project_elements_parent", "parent_id"),
        Index("idx_project_elements_status", "status"),
    )


class ElementDependency(Base):
    """Element Dependency model."""
    __tablename__ = "element_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    element_id = Column(
        UUID(as_uuid=True), ForeignKey("project_elements.id", ondelete="CASCADE"), nullable=False
    )
    depends_on_element_id = Column(
        UUID(as_uuid=True), ForeignKey("project_elements.id", ondelete="CASCADE"), nullable=False
    )
    dependency_type = Column(String, nullable=False)  # blocks, requires, related
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    element = relationship("ProjectElement", foreign_keys=[element_id], back_populates="dependencies")
    depends_on = relationship("ProjectElement", foreign_keys=[depends_on_element_id], back_populates="depends_on")

    __table_args__ = (
        UniqueConstraint("element_id", "depends_on_element_id"),
        Index("idx_dependencies_element", "element_id"),
        Index("idx_dependencies_depends_on", "depends_on_element_id"),
    )


class Feature(Base):
    """Feature model."""
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # new, in_progress, done, tested, merged
    progress_percentage = Column(Integer, default=0, nullable=False)
    total_todos = Column(Integer, default=0, nullable=False)
    completed_todos = Column(Integer, default=0, nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="features")
    todos = relationship("Todo", back_populates="feature", cascade="all, delete-orphan")
    feature_elements = relationship("FeatureElement", back_populates="feature", cascade="all, delete-orphan")
    github_branches = relationship("GitHubBranch", back_populates="feature")
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_features")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_features")

    __table_args__ = (
        Index("idx_features_project", "project_id"),
        Index("idx_features_status", "status"),
        Index("idx_features_assigned", "assigned_to"),
    )


class FeatureElement(Base):
    """Feature-Element relationship model."""
    __tablename__ = "feature_elements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(
        UUID(as_uuid=True), ForeignKey("project_elements.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    feature = relationship("Feature", back_populates="feature_elements")
    element = relationship("ProjectElement", back_populates="feature_elements")

    __table_args__ = (
        UniqueConstraint("feature_id", "element_id"),
        Index("idx_feature_elements_feature", "feature_id"),
        Index("idx_feature_elements_element", "element_id"),
    )


class Todo(Base):
    """Todo model."""
    __tablename__ = "todos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    element_id = Column(
        UUID(as_uuid=True), ForeignKey("project_elements.id", ondelete="CASCADE"), nullable=False
    )
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # new, in_progress, done
    position = Column(Integer, nullable=True)
    priority = Column(String, nullable=True, server_default='medium')  # low, medium, high, critical
    blocker_reason = Column(Text, nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking
    github_issue_number = Column(Integer, nullable=True)
    github_pr_number = Column(Integer, nullable=True)
    github_pr_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    element = relationship("ProjectElement", back_populates="todos")
    feature = relationship("Feature", back_populates="todos")
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_todos")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_todos")

    __table_args__ = (
        Index("idx_todos_element", "element_id"),
        Index("idx_todos_feature", "feature_id"),
        Index("idx_todos_status", "status"),
        Index("idx_todos_assigned", "assigned_to"),
        Index("idx_todos_created_by", "created_by"),
    )


class Document(Base):
    """Document model."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(UUID(as_uuid=True), ForeignKey("project_elements.id", ondelete="SET NULL"), nullable=True)
    type = Column(String, nullable=False, index=True)  # architecture, adr, domain, constraints, runbook, ai_instructions
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Markdown format
    tags = Column(ARRAY(String), default=[])
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="documents")
    element = relationship("ProjectElement", back_populates="documents")

    __table_args__ = (
        Index("idx_documents_project", "project_id"),
        Index("idx_documents_element", "element_id"),
        Index("idx_documents_type", "type"),
    )


class Session(Base):
    """Session model."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=True)
    goal = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    feature_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    todos_completed = Column(ARRAY(UUID(as_uuid=True)), default=[])
    features_completed = Column(ARRAY(UUID(as_uuid=True)), default=[])
    elements_updated = Column(ARRAY(UUID(as_uuid=True)), default=[])
    notes = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="sessions")
    user = relationship("User", foreign_keys=[user_id], back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_project", "project_id"),
        Index("idx_sessions_user", "user_id"),
    )


class Idea(Base):
    """Idea model."""
    __tablename__ = "ideas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # draft, active, archived
    tags = Column(ARRAY(String), default=[])
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)  # Team that owns this idea
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    converted_to_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="ideas")
    converted_to_project = relationship("Project", back_populates="ideas")

    __table_args__ = (
        Index("idx_ideas_team", "team_id"),
    )


class GitHubBranch(Base):
    """GitHub Branch model."""
    __tablename__ = "github_branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id", ondelete="SET NULL"), nullable=True)
    branch_name = Column(String, nullable=False)
    base_branch = Column(String, default="main", nullable=False)
    status = Column(String, nullable=False, index=True)  # active, merged, deleted
    ahead_count = Column(Integer, default=0, nullable=False)
    behind_count = Column(Integer, default=0, nullable=False)
    has_conflicts = Column(Boolean, default=False, nullable=False)
    last_commit_sha = Column(String, nullable=True)
    last_commit_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    merged_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="github_branches")
    feature = relationship("Feature", back_populates="github_branches")

    __table_args__ = (
        UniqueConstraint("project_id", "branch_name"),
        Index("idx_branches_project", "project_id"),
        Index("idx_branches_feature", "feature_id"),
        Index("idx_branches_status", "status"),
    )


class GitHubSync(Base):
    """GitHub Sync model."""
    __tablename__ = "github_sync"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String, nullable=False)  # element, todo, feature, branch
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    github_type = Column(String, nullable=False)  # issue, pr, branch, commit
    github_id = Column(Integer, nullable=True)
    github_url = Column(String, nullable=True)
    last_synced_at = Column(DateTime, server_default=func.now(), nullable=False)
    sync_direction = Column(String, nullable=False)  # tracker_to_github, github_to_tracker, bidirectional

    # Relationships
    project = relationship("Project", back_populates="github_syncs")

    __table_args__ = (
        UniqueConstraint("entity_id", "github_type", "github_id"),
        Index("idx_github_sync_project", "project_id"),
        Index("idx_github_sync_entity", "entity_type", "entity_id"),
    )


class Team(Base):
    """Team model."""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)  # 'hu' (Hungarian) or 'en' (English), immutable once set
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")
    ideas = relationship("Idea", back_populates="team", cascade="all, delete-orphan")
    invitation_codes = relationship("InvitationCode", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_teams_created_by", "created_by"),
    )


class TeamMember(Base):
    """Team Member model."""
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)  # team_leader, member
    joined_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

    __table_args__ = (
        UniqueConstraint("team_id", "user_id"),
        Index("idx_team_members_team", "team_id"),
        Index("idx_team_members_user", "user_id"),
    )


class InvitationCode(Base):
    """Invitation Code model."""
    __tablename__ = "invitation_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # admin, team
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    uses_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    used_at = Column(DateTime, nullable=True)  # When the invitation was used
    used_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Who used the invitation
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    team = relationship("Team", back_populates="invitation_codes")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_invitations")


class McpApiKey(Base):
    """MCP API Key model for user-specific MCP authentication."""
    __tablename__ = "mcp_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String, unique=True, nullable=False, index=True)  # Hashed version of the key for storage
    name = Column(String, nullable=True)  # Optional name/description for the key
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="mcp_api_keys")

    __table_args__ = (
        Index("idx_mcp_api_keys_user", "user_id"),
        Index("idx_mcp_api_keys_active", "is_active"),
    )
