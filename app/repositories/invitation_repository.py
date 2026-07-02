# ============================================================
# AETHER LINK - INVITATION REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
import secrets
import string

from .base import BaseRepository
from ..models.invitations import TeacherInvitation
from ..models.user import User


class InvitationRepository(BaseRepository[TeacherInvitation]):
    """Repository for TeacherInvitation model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, TeacherInvitation)
    
    # ============================================================
    # GENERATE TOKEN
    # ============================================================
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_token(self, token: str) -> Optional[TeacherInvitation]:
        """Get invitation by token."""
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.token == token,
            TeacherInvitation.deleted_at.is_(None)
        ).first()
    
    def get_by_token_or_fail(self, token: str) -> TeacherInvitation:
        """Get invitation by token or raise ValueError."""
        invitation = self.get_by_token(token)
        if not invitation:
            raise ValueError(f"Invitation with token {token} not found")
        return invitation
    
    def get_by_email(self, email: str) -> List[TeacherInvitation]:
        """Get all invitations for an email."""
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.email == email.lower(),
            TeacherInvitation.deleted_at.is_(None)
        ).order_by(TeacherInvitation.created_at.desc()).all()
    
    def get_by_email_and_valid(self, email: str) -> Optional[TeacherInvitation]:
        """Get valid (not expired, not accepted) invitation by email."""
        now = datetime.utcnow()
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.email == email.lower(),
            TeacherInvitation.accepted == False,
            TeacherInvitation.expires_at > now,
            TeacherInvitation.deleted_at.is_(None)
        ).first()
    
    def get_invited_by(self, invited_by: int) -> List[TeacherInvitation]:
        """Get invitations sent by a specific user."""
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.invited_by == invited_by,
            TeacherInvitation.deleted_at.is_(None)
        ).order_by(TeacherInvitation.created_at.desc()).all()
    
    def get_invited_by_paginated(
        self, 
        invited_by: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[TeacherInvitation], int]:
        """Get paginated invitations sent by a user."""
        query = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.invited_by == invited_by,
            TeacherInvitation.deleted_at.is_(None)
        ).order_by(TeacherInvitation.created_at.desc())
        total = query.count()
        invitations = query.offset(skip).limit(limit).all()
        return invitations, total
    
    # ============================================================
    # STATUS-BASED QUERIES
    # ============================================================
    
    def get_pending(self) -> List[TeacherInvitation]:
        """Get all pending (not accepted, not expired) invitations."""
        now = datetime.utcnow()
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.accepted == False,
            TeacherInvitation.expires_at > now,
            TeacherInvitation.deleted_at.is_(None)
        ).order_by(TeacherInvitation.created_at).all()
    
    def get_pending_count(self) -> int:
        """Get count of pending invitations."""
        now = datetime.utcnow()
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.accepted == False,
            TeacherInvitation.expires_at > now,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
    
    def get_expired(self) -> List[TeacherInvitation]:
        """Get expired invitations."""
        now = datetime.utcnow()
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.expires_at <= now,
            TeacherInvitation.accepted == False,
            TeacherInvitation.deleted_at.is_(None)
        ).order_by(TeacherInvitation.expires_at).all()
    
    def get_accepted(self) -> List[TeacherInvitation]:
        """Get accepted invitations."""
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.accepted == True,
            TeacherInvitation.deleted_at.is_(None)
        ).order_by(TeacherInvitation.accepted_at.desc()).all()
    
    # ============================================================
    # RELATIONSHIP QUERIES
    # ============================================================
    
    def get_with_inviter(self, invitation_id: int) -> Optional[TeacherInvitation]:
        """Get invitation with inviter loaded."""
        return self.db.query(TeacherInvitation).options(
            joinedload(TeacherInvitation.invited_by_user)
        ).filter(
            TeacherInvitation.id == invitation_id,
            TeacherInvitation.deleted_at.is_(None)
        ).first()
    
    def get_details(self, token: str) -> Optional[Dict[str, Any]]:
        """Get invitation details with inviter info."""
        invitation = self.db.query(TeacherInvitation).options(
            joinedload(TeacherInvitation.invited_by_user)
        ).filter(
            TeacherInvitation.token == token,
            TeacherInvitation.deleted_at.is_(None)
        ).first()
        
        if not invitation:
            return None
        
        return {
            "email": invitation.email,
            "full_name": invitation.full_name,
            "phone": invitation.phone,
            "token": invitation.token,
            "expires_at": invitation.expires_at,
            "is_expired": datetime.utcnow() > invitation.expires_at,
            "accepted": invitation.accepted,
            "invited_by": {
                "id": invitation.invited_by_user.id if invitation.invited_by_user else None,
                "name": invitation.invited_by_user.full_name if invitation.invited_by_user else None,
                "email": invitation.invited_by_user.email if invitation.invited_by_user else None,
            } if invitation.invited_by_user else None,
        }
    
    # ============================================================
    # VALIDATION OPERATIONS
    # ============================================================
    
    def is_email_invited(self, email: str) -> bool:
        """Check if an email has a pending invitation."""
        now = datetime.utcnow()
        invitation = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.email == email.lower(),
            TeacherInvitation.accepted == False,
            TeacherInvitation.expires_at > now,
            TeacherInvitation.deleted_at.is_(None)
        ).first()
        return invitation is not None
    
    def get_valid_token(self, token: str) -> Optional[TeacherInvitation]:
        """Get valid (not expired, not accepted) invitation by token."""
        now = datetime.utcnow()
        return self.db.query(TeacherInvitation).filter(
            TeacherInvitation.token == token,
            TeacherInvitation.accepted == False,
            TeacherInvitation.expires_at > now,
            TeacherInvitation.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def accept_invitation(self, token: str) -> TeacherInvitation:
        """Mark an invitation as accepted."""
        invitation = self.get_by_token_or_fail(token)
        
        if invitation.accepted:
            raise ValueError(f"Invitation already accepted")
        
        if datetime.utcnow() > invitation.expires_at:
            raise ValueError(f"Invitation has expired")
        
        invitation.accepted = True
        invitation.accepted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(invitation)
        return invitation
    
    def expire_invitation(self, invitation_id: int) -> TeacherInvitation:
        """Expire an invitation (set expiry to now)."""
        invitation = self.get_by_id_or_fail(invitation_id)
        
        invitation.expires_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(invitation)
        return invitation
    
    def regenerate_token(self, invitation_id: int, expiry_days: int = 7) -> TeacherInvitation:
        """Regenerate token for an invitation."""
        invitation = self.get_by_id_or_fail(invitation_id)
        
        # Generate new token
        invitation.token = self.generate_token()
        invitation.expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        invitation.accepted = False
        invitation.accepted_at = None
        
        self.db.commit()
        self.db.refresh(invitation)
        return invitation
    
    # ============================================================
    # CREATE WITH TOKEN
    # ============================================================
    
    def create_with_token(
        self, 
        email: str, 
        full_name: str, 
        invited_by: int,
        phone: Optional[str] = None,
        expiry_days: int = 7
    ) -> TeacherInvitation:
        """Create an invitation with generated token."""
        # Check if email already has pending invitation
        if self.is_email_invited(email):
            raise ValueError(f"Email {email} already has a pending invitation")
        
        token = self.generate_token()
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        invitation_data = {
            "email": email.lower(),
            "full_name": full_name,
            "phone": phone,
            "invited_by": invited_by,
            "token": token,
            "accepted": False,
            "expires_at": expires_at,
        }
        
        return self.create(**invitation_data)
    
    # ============================================================
    # COUNT & STATISTICS
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get invitation statistics."""
        now = datetime.utcnow()
        
        total = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        pending = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.accepted == False,
            TeacherInvitation.expires_at > now,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        accepted = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.accepted == True,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        expired = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.expires_at <= now,
            TeacherInvitation.accepted == False,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        return {
            "total": total,
            "pending": pending,
            "accepted": accepted,
            "expired": expired,
            "acceptance_rate": round(accepted / total * 100, 2) if total > 0 else 0,
        }
    
    def get_inviter_stats(self, inviter_id: int) -> Dict[str, Any]:
        """Get invitation statistics for a specific inviter."""
        total = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.invited_by == inviter_id,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        accepted = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.invited_by == inviter_id,
            TeacherInvitation.accepted == True,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        pending = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.invited_by == inviter_id,
            TeacherInvitation.accepted == False,
            TeacherInvitation.deleted_at.is_(None)
        ).count()
        
        return {
            "total": total,
            "accepted": accepted,
            "pending": pending,
            "acceptance_rate": round(accepted / total * 100, 2) if total > 0 else 0,
        }
    
    # ============================================================
    # CLEANUP
    # ============================================================
    
    def cleanup_expired(self) -> int:
        """Soft delete expired invitations."""
        now = datetime.utcnow()
        expired = self.db.query(TeacherInvitation).filter(
            TeacherInvitation.expires_at <= now,
            TeacherInvitation.accepted == False,
            TeacherInvitation.deleted_at.is_(None)
        ).all()
        
        count = 0
        for invitation in expired:
            self.soft_delete(invitation.id)
            count += 1
        
        return count