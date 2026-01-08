"""Team service."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models import Team, TeamMember, User


class TeamService:
    """Service for team operations."""

    @staticmethod
    def create_team(
        db: Session,
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
    ) -> Team:
        """Create a new team and assign creator as team leader."""
        # Check if team name already exists
        existing_team = db.query(Team).filter(Team.name == name).first()
        if existing_team:
            raise ValueError(f"Team with name '{name}' already exists")

        # Create team
        team = Team(
            name=name,
            description=description,
            created_by=created_by,
        )
        db.add(team)
        db.flush()  # Flush to get team.id

        # Add creator as team leader
        team_member = TeamMember(
            team_id=team.id,
            user_id=created_by,
            role="team_leader",
        )
        db.add(team_member)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def get_team_by_id(db: Session, team_id: UUID) -> Optional[Team]:
        """Get team by ID."""
        return db.query(Team).filter(Team.id == team_id).first()

    @staticmethod
    def list_teams(
        db: Session,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Team], int]:
        """List teams. If user_id provided, only return teams where user is a member."""
        if user_id:
            # Get teams where user is a member
            query = (
                db.query(Team)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
            )
        else:
            # Get all teams
            query = db.query(Team)

        total = query.count()
        teams = query.order_by(Team.created_at.desc()).offset(skip).limit(limit).all()
        return teams, total

    @staticmethod
    def update_team(
        db: Session,
        team_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Team]:
        """Update team."""
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None

        if name is not None:
            # Check if new name conflicts with existing team
            existing = db.query(Team).filter(Team.name == name, Team.id != team_id).first()
            if existing:
                raise ValueError(f"Team with name '{name}' already exists")
            team.name = name

        if description is not None:
            team.description = description

        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def delete_team(db: Session, team_id: UUID) -> bool:
        """Delete team and all members."""
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return False

        db.delete(team)  # Cascade will delete team members
        db.commit()
        return True

    @staticmethod
    def add_member(
        db: Session,
        team_id: UUID,
        user_id: UUID,
        role: str = "member",
    ) -> TeamMember:
        """Add a member to a team."""
        # Verify team exists
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check if user is already a member
        existing = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if existing:
            raise ValueError(f"User {user_id} is already a member of team {team_id}")

        # Validate role
        if role not in ["team_leader", "member"]:
            raise ValueError(f"Invalid role: {role}. Must be 'team_leader' or 'member'")

        team_member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
        )
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        return team_member

    @staticmethod
    def remove_member(
        db: Session,
        team_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Remove a member from a team.
        
        Non-admin users must remain members of at least one team.
        If removing from the last team, an error is raised.
        """
        team_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if not team_member:
            return False

        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "admin":
            # Admins can be removed from teams (they don't need team membership)
            db.delete(team_member)
            db.commit()
            return True
        
        # For non-admin users, check if this is their last team
        other_teams = (
            db.query(TeamMember)
            .filter(
                TeamMember.user_id == user_id,
                TeamMember.team_id != team_id
            )
            .count()
        )
        
        if other_teams == 0:
            raise ValueError(
                "Cannot remove user from team: non-admin users must be members of at least one team. "
                "Add user to another team first, or change user role to admin."
            )

        db.delete(team_member)
        db.commit()
        return True

    @staticmethod
    def update_member_role(
        db: Session,
        team_id: UUID,
        user_id: UUID,
        role: str,
    ) -> Optional[TeamMember]:
        """Update a team member's role."""
        if role not in ["team_leader", "member"]:
            raise ValueError(f"Invalid role: {role}. Must be 'team_leader' or 'member'")

        team_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if not team_member:
            return None

        team_member.role = role
        db.commit()
        db.refresh(team_member)
        return team_member

    @staticmethod
    def get_team_members(
        db: Session,
        team_id: UUID,
    ) -> List[TeamMember]:
        """Get all members of a team."""
        return (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id)
            .order_by(TeamMember.joined_at.asc())
            .all()
        )

    @staticmethod
    def is_team_leader(
        db: Session,
        team_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Check if user is a team leader of the team."""
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.role == "team_leader",
            )
            .first()
        )
        return team_member is not None

    @staticmethod
    def is_team_member(
        db: Session,
        team_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Check if user is a member of the team (any role)."""
        team_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        return team_member is not None

    @staticmethod
    def has_team_membership(
        db: Session,
        user_id: UUID,
    ) -> bool:
        """Check if user is a member of any team."""
        team_member = (
            db.query(TeamMember)
            .filter(TeamMember.user_id == user_id)
            .first()
        )
        return team_member is not None
