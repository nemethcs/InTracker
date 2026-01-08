"""Invitation code service."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models import InvitationCode, User, Team


class InvitationService:
    """Service for invitation code operations."""

    @staticmethod
    def generate_code(length: int = 32) -> str:
        """Generate a secure random invitation code."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_admin_invitation(
        db: Session,
        created_by: UUID,
        expires_in_days: Optional[int] = 30,
    ) -> InvitationCode:
        """Generate an admin invitation code.
        
        Admin invitations allow users to register with admin privileges
        and create teams.
        """
        code = InvitationService.generate_code()
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        invitation = InvitationCode(
            code=code,
            type="admin",
            team_id=None,
            created_by=created_by,
            expires_at=expires_at,
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def generate_team_invitation(
        db: Session,
        team_id: UUID,
        created_by: UUID,
        expires_in_days: Optional[int] = 7,
    ) -> InvitationCode:
        """Generate a team invitation code.
        
        Team invitations allow users to register and automatically join
        the specified team as a member.
        """
        # Verify team exists
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        code = InvitationService.generate_code()
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        invitation = InvitationCode(
            code=code,
            type="team",
            team_id=team_id,
            created_by=created_by,
            expires_at=expires_at,
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def validate_code(db: Session, code: str) -> tuple[bool, Optional[InvitationCode], Optional[str]]:
        """Validate an invitation code.
        
        Returns:
            tuple: (is_valid, invitation_code, error_message)
        """
        invitation = db.query(InvitationCode).filter(InvitationCode.code == code).first()
        
        if not invitation:
            return False, None, "Invalid invitation code"
        
        if invitation.used_at is not None:
            return False, invitation, "Invitation code has already been used"
        
        if invitation.expires_at and invitation.expires_at < datetime.utcnow():
            return False, invitation, "Invitation code has expired"
        
        return True, invitation, None

    @staticmethod
    def mark_as_used(
        db: Session,
        code: str,
        user_id: UUID,
    ) -> InvitationCode:
        """Mark an invitation code as used by a user."""
        invitation = db.query(InvitationCode).filter(InvitationCode.code == code).first()
        
        if not invitation:
            raise ValueError(f"Invitation code {code} not found")
        
        if invitation.used_at is not None:
            raise ValueError(f"Invitation code {code} has already been used")
        
        invitation.used_at = datetime.utcnow()
        invitation.used_by = user_id
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def get_invitation_by_code(db: Session, code: str) -> Optional[InvitationCode]:
        """Get invitation by code."""
        return db.query(InvitationCode).filter(InvitationCode.code == code).first()

    @staticmethod
    def get_invitations_by_creator(
        db: Session,
        created_by: UUID,
        type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[InvitationCode], int]:
        """Get invitations created by a user."""
        query = db.query(InvitationCode).filter(InvitationCode.created_by == created_by)
        
        if type:
            query = query.filter(InvitationCode.type == type)
        
        total = query.count()
        invitations = query.order_by(InvitationCode.created_at.desc()).offset(skip).limit(limit).all()
        
        return invitations, total

    @staticmethod
    def get_all_invitations(
        db: Session,
        type: Optional[str] = None,
        used: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[InvitationCode], int]:
        """Get all invitations (admin only)."""
        query = db.query(InvitationCode)
        
        if type:
            query = query.filter(InvitationCode.type == type)
        
        if used is not None:
            if used:
                query = query.filter(InvitationCode.used_at.isnot(None))
            else:
                query = query.filter(InvitationCode.used_at.is_(None))
        
        total = query.count()
        invitations = query.order_by(InvitationCode.created_at.desc()).offset(skip).limit(limit).all()
        
        return invitations, total

    @staticmethod
    def delete_invitation(db: Session, code: str) -> bool:
        """Delete an invitation code."""
        invitation = db.query(InvitationCode).filter(InvitationCode.code == code).first()
        
        if not invitation:
            return False
        
        if invitation.used_at is not None:
            raise ValueError("Cannot delete a used invitation code")
        
        db.delete(invitation)
        db.commit()
        return True
