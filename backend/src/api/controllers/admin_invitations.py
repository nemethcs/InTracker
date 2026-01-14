"""Admin invitation management endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.services.invitation_service import InvitationService
from src.api.middleware.auth import get_current_admin_user

# Import shared router from admin_controller
from .admin_controller import router


@router.post("/invitations/admin", status_code=status.HTTP_201_CREATED)
async def create_admin_invitation(
    expires_in_days: Optional[int] = Query(30, ge=1, le=365),
    send_email_to: Optional[str] = Query(None, description="Email address to send invitation to"),
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create an admin invitation code. Requires admin role.
    
    Admin invitations allow users to register with team_leader role
    and automatically create their own team.
    """
    import logging
    from src.services.email_service import email_service
    from src.config import settings
    
    logger = logging.getLogger(__name__)
    
    try:
        invitation = InvitationService.generate_admin_invitation(
            db=db,
            created_by=UUID(current_user["user_id"]),
            expires_in_days=expires_in_days,
        )
        
        # Send email if email address provided
        if send_email_to:
            # Build invitation URL
            frontend_url = settings.FRONTEND_URL
            if not frontend_url or frontend_url == "*":
                frontend_url = "https://intracker.kesmarki.com"
            invitation_url = f"{frontend_url}/register?code={invitation.code}"
            
            # Get inviter name
            inviter_name = current_user.get("name") or current_user.get("email", "Admin")
            
            # Build email content for team leader invitation
            expires_text = f" This invitation expires in {expires_in_days} days." if expires_in_days else ""
            
            subject = "Invitation to become a Team Leader on InTracker"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Team Leader Invitation</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h1 style="color: #2563eb; margin-top: 0;">You've been invited to become a Team Leader!</h1>
                </div>
                
                <div style="background-color: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                    <p>Hello,</p>
                    
                    <p>You've been invited by <strong>{inviter_name}</strong> to join InTracker as a Team Leader.{expires_text}</p>
                    
                    <p>As a Team Leader, you will be able to:</p>
                    <ul style="color: #6b7280; font-size: 14px;">
                        <li>Create and manage your own team</li>
                        <li>Invite members to your team</li>
                        <li>Manage projects and track progress</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{invitation_url}" 
                           style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                            Accept Invitation
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px;">
                        Or copy and paste this link into your browser:<br>
                        <a href="{invitation_url}" style="color: #2563eb; word-break: break-all;">{invitation_url}</a>
                    </p>
                    
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        Your invitation code: <code style="background-color: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{invitation.code}</code>
                    </p>
                </div>
                
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; text-align: center;">
                    <p>This is an automated message from InTracker. Please do not reply to this email.</p>
                </div>
            </body>
            </html>
            """
            
            plain_text_content = f"""
You've been invited by {inviter_name} to join InTracker as a Team Leader.{expires_text}

As a Team Leader, you will be able to:
- Create and manage your own team
- Invite members to your team
- Manage projects and track progress

Click here to accept: {invitation_url}

Your invitation code: {invitation.code}

This is an automated message from InTracker. Please do not reply to this email.
            """.strip()
            
            email_sent = email_service.send_email(
                to_email=send_email_to,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content,
            )
            
            if not email_sent:
                logger.warning(f"Failed to send team leader invitation email to {send_email_to}, but invitation was created")
        
        return {
            "message": "Admin invitation code created successfully",
            "status": "success",
            "invitation": {
                "code": invitation.code,
                "type": invitation.type,
                "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
                "created_at": invitation.created_at.isoformat(),
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin invitation: {str(e)}",
        )


@router.get("/invitations", status_code=status.HTTP_200_OK)
async def list_invitations(
    type: Optional[str] = Query(None, description="Filter by type (admin, team)"),
    used: Optional[bool] = Query(None, description="Filter by used status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """List all invitations. Requires admin role."""
    invitations, total = InvitationService.get_all_invitations(
        db=db,
        type=type,
        used=used,
        skip=skip,
        limit=limit,
    )

    return {
        "invitations": [
            {
                "code": invitation.code,
                "type": invitation.type,
                "team_id": str(invitation.team_id) if invitation.team_id else None,
                "created_by": str(invitation.created_by),
                "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
                "used_at": invitation.used_at.isoformat() if invitation.used_at else None,
                "used_by": str(invitation.used_by) if invitation.used_by else None,
                "created_at": invitation.created_at.isoformat(),
            }
            for invitation in invitations
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/invitations/{code}", status_code=status.HTTP_200_OK)
async def get_invitation(
    code: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get invitation by code. Requires admin role."""
    invitation = InvitationService.get_invitation_by_code(db=db, code=code)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation code {code} not found",
        )

    return {
        "code": invitation.code,
        "type": invitation.type,
        "team_id": str(invitation.team_id) if invitation.team_id else None,
        "created_by": str(invitation.created_by),
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
        "used_at": invitation.used_at.isoformat() if invitation.used_at else None,
        "used_by": str(invitation.used_by) if invitation.used_by else None,
        "created_at": invitation.created_at.isoformat(),
    }


@router.delete("/invitations/{code}", status_code=status.HTTP_200_OK)
async def delete_invitation(
    code: str,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an invitation code. Requires admin role."""
    try:
        success = InvitationService.delete_invitation(db=db, code=code)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invitation code {code} not found",
            )

        return {
            "message": f"Invitation code {code} deleted successfully",
            "status": "success",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete invitation: {str(e)}",
        )
