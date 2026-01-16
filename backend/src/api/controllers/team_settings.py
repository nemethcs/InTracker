"""Team settings endpoints (language, invitations)."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models import User
from src.services.team_service import TeamService
from src.services.invitation_service import InvitationService
from src.services.email_service import email_service
from src.api.middleware.auth import get_current_team_leader
from src.config import settings
from src.api.schemas.team import (
    TeamResponse,
    TeamLanguageRequest,
    TeamInvitationResponse,
)

# Import shared router from team_controller
# Note: Import at end to avoid circular import
from .team_controller import router  # noqa: E402


@router.post("/{team_id}/language", response_model=TeamResponse, status_code=status.HTTP_200_OK)
async def set_team_language(
    team_id: UUID,
    request: TeamLanguageRequest,
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Set team language. Only team leaders can set language, and it can only be set once."""
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can set team language",
        )

    try:
        team = TeamService.set_team_language(
            db=db,
            team_id=team_id,
            language=request.language,
        )
        # Convert UUIDs to strings for response
        return {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "language": team.language,
            "created_by": str(team.created_by),
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{team_id}/invitations", response_model=TeamInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_team_invitation(
    team_id: UUID,
    expires_in_days: Optional[int] = Query(7, ge=1, le=365),
    send_email_to: Optional[str] = Query(None, description="Email address to send invitation to"),
    member_role: str = Query("member", description="Role for the invited user (member or team_leader)"),
    current_user: dict = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    """Create a team invitation code. Only team leaders or admins can create invitations.
    
    Args:
        team_id: Team ID
        expires_in_days: Number of days until invitation expires (default: 7)
        send_email_to: Optional email address to send invitation to
        member_role: Role for the invited user (member or team_leader). Default: member.
                    Only admins can create team_leader invitations.
    """
    user_role = current_user.get("role")
    current_user_id = UUID(current_user["user_id"])

    # Check if user is admin or team leader
    if user_role != "admin" and not TeamService.is_team_leader(db, team_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or admins can create team invitations",
        )
    
    # Validate member_role
    if member_role not in ["member", "team_leader"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid member_role. Must be 'member' or 'team_leader'",
        )
    
    # Only admins can create team_leader invitations
    if member_role == "team_leader" and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create team leader invitations",
        )

    try:
        # Get team and inviter info
        team = TeamService.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        
        inviter = db.query(User).filter(User.id == current_user_id).first()
        inviter_name = inviter.name if inviter else None

        # If email is provided, check if user already exists
        existing_user = None
        if send_email_to:
            existing_user = db.query(User).filter(User.email.ilike(send_email_to)).first()
            
            # If user exists and is not already a team member, add them directly
            if existing_user:
                from src.database.models import TeamMember
                existing_member = db.query(TeamMember).filter(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == existing_user.id
                ).first()
                
                if existing_member:
                    # User is already a team member
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"User with email {send_email_to} is already a member of this team",
                    )
                else:
                    # Add existing user directly to team
                    team_member = TeamService.add_member(
                        db=db,
                        team_id=team_id,
                        user_id=existing_user.id,
                        role=member_role,
                    )
                    # Send notification email to existing user
                    frontend_url = settings.FRONTEND_URL
                    if not frontend_url or frontend_url == "*":
                        frontend_url = "https://intracker.kesmarki.com"
                    team_url = f"{frontend_url}/teams"
                    
                    inviter_text = f" from {inviter_name}" if inviter_name else ""
                    subject = f"You've been added to {team.name} on InTracker"
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Team Member Added</title>
                    </head>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h1 style="color: #2563eb; margin-top: 0;">You've been added to {team.name}!</h1>
                        </div>
                        
                        <div style="background-color: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                            <p>Hello,</p>
                            
                            <p>You've been added{inviter_text} to <strong>{team.name}</strong> on InTracker as a <strong>{member_role}</strong>.</p>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{team_url}" 
                                   style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                                    View Team
                                </a>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; text-align: center;">
                            <p>This is an automated message from InTracker. Please do not reply to this email.</p>
                        </div>
                    </body>
                    </html>
                    """
                    plain_text_content = f"""
You've been added{inviter_text} to {team.name} on InTracker as a {member_role}.

View your team: {team_url}

This is an automated message from InTracker. Please do not reply to this email.
                    """.strip()
                    
                    email_sent = email_service.send_email(
                        to_email=send_email_to,
                        subject=subject,
                        html_content=html_content,
                        plain_text_content=plain_text_content,
                    )
                    
                    # Return invitation response with special code to indicate direct add
                    # Frontend can check if code starts with "DIRECT_ADD:" to know user was added directly
                    return TeamInvitationResponse(
                        code=f"DIRECT_ADD:{team_member.id}",  # Special code to indicate direct add
                        type="team",
                        team_id=str(team_id),
                        expires_at=None,
                        created_at=team_member.joined_at.isoformat() if team_member.joined_at else datetime.utcnow().isoformat(),
                        email_sent_to=send_email_to,
                        email_sent_at=datetime.utcnow().isoformat() if email_sent else None,
                    )

        # User doesn't exist, create invitation
        invitation = InvitationService.generate_team_invitation(
            db=db,
            team_id=team_id,
            created_by=current_user_id,
            expires_in_days=expires_in_days,
            member_role=member_role,
        )
        
        # Send email if email address provided
        if send_email_to:
            # Check if email was already sent to this address for this invitation
            if invitation.email_sent_to and invitation.email_sent_to.lower() == send_email_to.lower():
                # Email already sent, don't send again
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Invitation email already sent to {send_email_to} for invitation {invitation.code}")
            else:
                from src.services.email_service import email_service
                from datetime import datetime
                email_sent = email_service.send_invitation_email(
                    to_email=send_email_to,
                    invitation_code=invitation.code,
                    team_name=team.name,
                    inviter_name=inviter_name,
                    expires_in_days=expires_in_days,
                )
                if email_sent:
                    # Mark email as sent
                    invitation.email_sent_to = send_email_to
                    invitation.email_sent_at = datetime.utcnow()
                    db.commit()
                else:
                    # Log warning but don't fail the request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to send invitation email to {send_email_to}, but invitation was created")
        
        return TeamInvitationResponse(
            code=invitation.code,
            type=invitation.type,
            team_id=str(invitation.team_id) if invitation.team_id else None,
            expires_at=invitation.expires_at.isoformat() if invitation.expires_at else None,
            created_at=invitation.created_at.isoformat(),
            email_sent_to=invitation.email_sent_to,
            email_sent_at=invitation.email_sent_at.isoformat() if invitation.email_sent_at else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
