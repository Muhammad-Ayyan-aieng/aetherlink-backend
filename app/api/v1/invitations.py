# ============================================================
# AETHER LINK - INVITATIONS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any

from ...core.database import get_db
from ...core.dependencies import (
    get_current_user,
    get_current_admin_user,
    rate_limiter,
)
from ...services.invitation_service import InvitationService
from ...schemas.invitation import (
    InviteTeacher,
    AcceptInvitation,
    ResendInvitation,
    InvitationResponse,
    InvitationListResponse,
    InvitationSummary,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/invitations", tags=["Invitations"])


# ============================================================
# ADMIN: SEND INVITATION
# ============================================================

@router.post(
    "/",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin_user)],
    summary="Send teacher invitation",
    description="Send a teacher invitation (admin only).",
)
def send_invitation(
    invite_data: InviteTeacher,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Send a teacher invitation.
    
    **Admin only.**
    
    - **email**: Teacher's email address
    - **full_name**: Teacher's full name
    - **phone**: Optional phone number
    - **expiry_days**: Invitation expiry in days (1-30)
    """
    try:
        invitation_service = InvitationService(db)
        result = invitation_service.send_invitation(
            invite_data=invite_data,
            admin_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# PUBLIC: VERIFY INVITATION
# ============================================================

@router.get(
    "/verify/{token}",
    dependencies=[Depends(rate_limiter)],
    summary="Verify invitation token",
    description="Verify an invitation token.",
)
def verify_invitation(
    token: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Verify an invitation token.
    
    - **token**: Invitation token
    """
    try:
        invitation_service = InvitationService(db)
        details = invitation_service.get_invitation_details(token)
        
        return {
            "valid": True,
            "email": details["email"],
            "full_name": details["full_name"],
            "expires_at": details["expires_at"],
            "is_expired": details["is_expired"],
            "invited_by": details["invited_by"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# PUBLIC: ACCEPT INVITATION
# ============================================================

@router.post(
    "/accept",
    dependencies=[Depends(rate_limiter)],
    summary="Accept invitation",
    description="Accept an invitation and create teacher account.",
)
def accept_invitation(
    accept_data: AcceptInvitation,
    db: Session = Depends(get_db),
) -> Any:
    """
    Accept an invitation and create teacher account.
    
    - **token**: Invitation token
    - **password**: Password (8-72 characters)
    - **username**: Unique username
    """
    try:
        invitation_service = InvitationService(db)
        result = invitation_service.accept_invitation(accept_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: LIST INVITATIONS
# ============================================================

@router.get(
    "/",
    response_model=InvitationListResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="List invitations",
    description="List all invitations (admin only).",
)
def list_invitations(
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, expired, all"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    List all invitations.
    
    **Admin only.**
    
    - **status**: Filter by status
    - **skip**: Pagination offset
    - **limit**: Max results (1-100)
    """
    try:
        invitation_service = InvitationService(db)
        
        if status == "pending":
            invitations = invitation_service.invitation_repo.get_pending()
            total = len(invitations)
            invitations = invitations[skip:skip + limit]
        elif status == "accepted":
            invitations = invitation_service.invitation_repo.get_accepted()
            total = len(invitations)
            invitations = invitations[skip:skip + limit]
        elif status == "expired":
            invitations = invitation_service.invitation_repo.get_expired()
            total = len(invitations)
            invitations = invitations[skip:skip + limit]
        else:
            # All invitations
            result = invitation_service.get_sent_invitations(
                admin_id=current_user.id,
                skip=skip,
                limit=limit,
            )
            return result
        
        return {
            "invitations": [invitation_service._format_invitation_response(i) for i in invitations],
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: RESEND INVITATION
# ============================================================

@router.post(
    "/{invitation_id}/resend",
    response_model=InvitationResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Resend invitation",
    description="Resend an invitation (admin only).",
)
def resend_invitation(
    invitation_id: int,
    resend_data: ResendInvitation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Resend an invitation.
    
    **Admin only.**
    
    - **invitation_id**: Invitation ID
    - **expiry_days**: New expiry in days (1-30)
    """
    try:
        # Merge path param with body
        resend_data.invitation_id = invitation_id
        
        invitation_service = InvitationService(db)
        result = invitation_service.resend_invitation(
            resend_data=resend_data,
            admin_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: CANCEL INVITATION
# ============================================================

@router.delete(
    "/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin_user)],
    summary="Cancel invitation",
    description="Cancel an invitation (admin only).",
)
def cancel_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Cancel an invitation.
    
    **Admin only.**
    
    - **invitation_id**: Invitation ID
    """
    try:
        invitation_service = InvitationService(db)
        invitation_service.cancel_invitation(
            invitation_id=invitation_id,
            admin_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: INVITATION STATISTICS
# ============================================================

@router.get(
    "/stats",
    response_model=InvitationSummary,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get invitation statistics",
    description="Get invitation statistics (admin only).",
)
def get_invitation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get invitation statistics.
    
    **Admin only.**
    """
    try:
        invitation_service = InvitationService(db)
        stats = invitation_service.get_invitation_stats(current_user.id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: MY INVITATION STATS
# ============================================================

@router.get(
    "/my-stats",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get my invitation statistics",
    description="Get invitation statistics for the current admin.",
)
def get_my_invitation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get invitation statistics for the current admin.
    
    **Admin only.**
    """
    try:
        invitation_service = InvitationService(db)
        stats = invitation_service.get_admin_invitation_stats(current_user.id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: CLEANUP EXPIRED
# ============================================================

@router.post(
    "/cleanup",
    dependencies=[Depends(get_current_admin_user)],
    summary="Cleanup expired invitations",
    description="Clean up expired invitations (admin only).",
)
def cleanup_expired(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Clean up expired invitations.
    
    **Admin only.**
    """
    try:
        invitation_service = InvitationService(db)
        result = invitation_service.cleanup_expired_invitations(current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )