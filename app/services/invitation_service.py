# ============================================================
# AETHER LINK - INVITATION SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import html

from ..repositories.invitation_repository import InvitationRepository
from ..repositories.user_repository import UserRepository
from ..models.user import UserRole
from ..schemas.invitation import InviteTeacher, AcceptInvitation, ResendInvitation


class InvitationService:
    """Service for invitation business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.invitation_repo = InvitationRepository(db)
        self.user_repo = UserRepository(db)
    
    # ============================================================
    # SEND INVITATION (Admin)
    # ============================================================
    
    def send_invitation(self, invite_data: InviteTeacher, admin_id: int) -> Dict[str, Any]:
        """
        Send a teacher invitation (admin only).
        
        Args:
            invite_data: Invitation data
            admin_id: Admin ID
            
        Returns:
            Invitation details
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        # Check if email already has a pending invitation
        if self.invitation_repo.is_email_invited(invite_data.email):
            raise ValueError(f"Email {invite_data.email} already has a pending invitation")
        
        # Check if email is already registered as a user
        if self.user_repo.is_email_taken(invite_data.email):
            raise ValueError(f"Email {invite_data.email} is already registered")
        
        # Check if email is already a teacher
        user = self.user_repo.get_by_email(invite_data.email)
        if user and user.role == UserRole.TEACHER:
            raise ValueError(f"Email {invite_data.email} is already a teacher")
        
        # Sanitize name
        full_name = html.escape(invite_data.full_name.strip())
        if len(full_name) < 1 or len(full_name) > 100:
            raise ValueError("Full name must be between 1 and 100 characters")
        
        # Validate phone if provided
        phone = None
        if invite_data.phone:
            import re
            cleaned = re.sub(r'[\s\-\(\)]', '', invite_data.phone)
            if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
                raise ValueError("Invalid phone number format")
            phone = invite_data.phone
        
        # Create invitation
        invitation = self.invitation_repo.create_with_token(
            email=invite_data.email.lower(),
            full_name=full_name,
            invited_by=admin_id,
            phone=phone,
            expiry_days=invite_data.expiry_days,
        )
        
        # TODO: Send email with invitation link
        # For now, just return the invitation
        
        return self._format_invitation_response(invitation)
    
    # ============================================================
    # GET INVITATION (By Token)
    # ============================================================
    
    def get_invitation(self, token: str) -> Dict[str, Any]:
        """
        Get invitation by token.
        
        Args:
            token: Invitation token
            
        Returns:
            Invitation details
            
        Raises:
            ValueError: If invitation not found
        """
        invitation = self.invitation_repo.get_by_token(token)
        if not invitation:
            raise ValueError("Invalid invitation token")
        
        return self._format_invitation_response(invitation)
    
    def get_invitation_details(self, token: str) -> Dict[str, Any]:
        """
        Get invitation details with inviter info.
        
        Args:
            token: Invitation token
            
        Returns:
            Invitation details
            
        Raises:
            ValueError: If invitation not found
        """
        details = self.invitation_repo.get_details(token)
        if not details:
            raise ValueError("Invalid invitation token")
        
        return details
    
    # ============================================================
    # ACCEPT INVITATION (Teacher)
    # ============================================================
    
    def accept_invitation(self, accept_data: AcceptInvitation) -> Dict[str, Any]:
        """
        Accept an invitation and create teacher account.
        
        Args:
            accept_data: Acceptance data
            
        Returns:
            Created teacher user
            
        Raises:
            ValueError: If validation fails
        """
        # Get valid invitation
        invitation = self.invitation_repo.get_valid_token(accept_data.token)
        if not invitation:
            raise ValueError("Invalid or expired invitation token")
        
        # Check if email already registered
        if self.user_repo.is_email_taken(invitation.email):
            raise ValueError("Email already registered")
        
        # Check if username taken
        if self.user_repo.is_username_taken(accept_data.username):
            raise ValueError("Username already taken")
        
        # Validate username
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', accept_data.username):
            raise ValueError("Username must contain only letters, numbers, and underscores")
        
        # Validate password (basic check)
        if len(accept_data.password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(accept_data.password) > 72:
            raise ValueError("Password must be less than 72 characters")
        
        # Create teacher user
        from ..core.security import get_password_hash, validate_password_strength
        
        # Validate password strength
        password_check = validate_password_strength(accept_data.password)
        if not password_check["is_strong"]:
            raise ValueError(f"Password too weak: {', '.join(password_check['errors'])}")
        
        hashed_password = get_password_hash(accept_data.password)
        
        # Create user
        user = self.user_repo.create(
            email=invitation.email,
            username=accept_data.username.lower(),
            hashed_password=hashed_password,
            full_name=invitation.full_name,
            phone=invitation.phone,
            role=UserRole.TEACHER,
            is_verified=True,
            is_active=True,
        )
        
        # Mark invitation as accepted
        self.invitation_repo.accept_invitation(accept_data.token)
        
        # TODO: Send welcome email
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
            },
            "message": "Account created successfully. Please login.",
        }
    
    # ============================================================
    # RESEND INVITATION (Admin)
    # ============================================================
    
    def resend_invitation(self, resend_data: ResendInvitation, admin_id: int) -> Dict[str, Any]:
        """
        Resend an invitation (admin only).
        
        Args:
            resend_data: Resend data
            admin_id: Admin ID
            
        Returns:
            Updated invitation
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        # Check invitation exists
        invitation = self.invitation_repo.get_by_id(resend_data.invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")
        
        # Check if already accepted
        if invitation.accepted:
            raise ValueError("Invitation already accepted")
        
        # Check if email already registered
        if self.user_repo.is_email_taken(invitation.email):
            raise ValueError("Email already registered")
        
        # Check if email already has a pending invitation
        if self.invitation_repo.is_email_invited(invitation.email):
            # Get the existing pending invitation
            existing = self.invitation_repo.get_by_email_and_valid(invitation.email)
            if existing and existing.id != invitation.id:
                raise ValueError(f"Email {invitation.email} already has a pending invitation")
        
        # Regenerate token
        invitation = self.invitation_repo.regenerate_token(
            invitation_id=resend_data.invitation_id,
            expiry_days=resend_data.expiry_days,
        )
        
        # TODO: Resend email with new invitation link
        
        return self._format_invitation_response(invitation)
    
    # ============================================================
    # CANCEL INVITATION (Admin)
    # ============================================================
    
    def cancel_invitation(self, invitation_id: int, admin_id: int) -> Dict[str, Any]:
        """
        Cancel an invitation (admin only).
        
        Args:
            invitation_id: Invitation ID
            admin_id: Admin ID
            
        Returns:
            Success message
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        # Check invitation exists
        invitation = self.invitation_repo.get_by_id(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")
        
        if invitation.accepted:
            raise ValueError("Invitation already accepted")
        
        # Soft delete invitation
        self.invitation_repo.soft_delete(invitation_id)
        
        return {"message": "Invitation cancelled successfully"}
    
    # ============================================================
    # GET PENDING INVITATIONS (Admin)
    # ============================================================
    
    def get_pending_invitations(
        self, 
        admin_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get pending invitations (admin only).
        
        Args:
            admin_id: Admin ID
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Pending invitations
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        if limit > 100:
            limit = 100
        
        invitations = self.invitation_repo.get_pending()
        total = len(invitations)
        
        # Apply pagination
        invitations = invitations[skip:skip + limit]
        
        return {
            "invitations": [self._format_invitation_response(i) for i in invitations],
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    def get_sent_invitations(
        self, 
        admin_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get all invitations sent by an admin.
        
        Args:
            admin_id: Admin ID
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Invitations
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        if limit > 100:
            limit = 100
        
        invitations, total = self.invitation_repo.get_invited_by_paginated(admin_id, skip, limit)
        
        return {
            "invitations": [self._format_invitation_response(i) for i in invitations],
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    # ============================================================
    # STATISTICS (Admin)
    # ============================================================
    
    def get_invitation_stats(self, admin_id: int) -> Dict[str, Any]:
        """
        Get invitation statistics (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Invitation statistics
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.invitation_repo.get_stats()
    
    def get_admin_invitation_stats(self, admin_id: int) -> Dict[str, Any]:
        """
        Get invitation statistics for a specific admin.
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Invitation statistics for admin
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.invitation_repo.get_inviter_stats(admin_id)
    
    # ============================================================
    # CLEANUP (Admin)
    # ============================================================
    
    def cleanup_expired_invitations(self, admin_id: int) -> Dict[str, Any]:
        """
        Clean up expired invitations (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Cleanup results
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        count = self.invitation_repo.cleanup_expired()
        
        return {
            "message": f"Cleaned up {count} expired invitations",
            "count": count,
        }
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _format_invitation_response(self, invitation: Any) -> Dict[str, Any]:
        """Format invitation for response."""
        now = datetime.utcnow()
        is_expired = invitation.expires_at <= now
        
        return {
            "id": invitation.id,
            "email": invitation.email,
            "full_name": invitation.full_name,
            "phone": invitation.phone,
            "invited_by": invitation.invited_by,
            "invited_by_name": invitation.invited_by_user.full_name if invitation.invited_by_user else None,
            "token": invitation.token,
            "accepted": invitation.accepted,
            "accepted_at": invitation.accepted_at,
            "expires_at": invitation.expires_at,
            "is_expired": is_expired,
            "days_until_expiry": max(0, (invitation.expires_at - now).days) if not is_expired else 0,
            "created_at": invitation.created_at,
            "updated_at": invitation.updated_at,
        }