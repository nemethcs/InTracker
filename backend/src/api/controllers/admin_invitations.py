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
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create an admin invitation code. Requires admin role."""
    try:
        invitation = InvitationService.generate_admin_invitation(
            db=db,
            created_by=UUID(current_user["user_id"]),
            expires_in_days=expires_in_days,
        )
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
