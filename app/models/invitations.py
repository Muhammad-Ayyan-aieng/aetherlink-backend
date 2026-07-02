# ============================================================
# AETHER LINK - TEACHER INVITATION MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class TeacherInvitation(Base):
    __tablename__ = "teacher_invitations"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # INVITATION DETAILS
    # ============================================================
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # ============================================================
    # INVITER
    # ============================================================
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ============================================================
    # SECURE TOKEN
    # ============================================================
    token = Column(String(255), unique=True, index=True, nullable=False)
    
    # ============================================================
    # STATUS
    # ============================================================
    accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # EXPIRY
    # ============================================================
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_teacher_invitations_email', 'email'),
        Index('ix_teacher_invitations_token', 'token'),
        Index('ix_teacher_invitations_accepted', 'accepted'),
        Index('ix_teacher_invitations_expires', 'expires_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    invited_by_user = relationship(
        "User",
        foreign_keys=[invited_by]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<TeacherInvitation {self.email}>"
    
    def __str__(self) -> str:
        return f"Invitation for {self.full_name} ({self.email})"
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return func.now() > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return not self.accepted and not self.is_expired
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiry."""
        if self.is_expired:
            return 0
        # Calculate days difference
        delta = self.expires_at - func.now()
        return delta.days if delta.days > 0 else 0
    
    def accept(self) -> None:
        """Mark invitation as accepted."""
        self.accepted = True
        self.accepted_at = func.now()
    
    def regenerate_token(self, new_token: str, expiry_days: int = 7) -> None:
        """
        Regenerate token and reset expiry.
        Used for resending invitations.
        """
        self.token = new_token
        self.expires_at = func.now() + func.interval(f'{expiry_days} days')
        self.accepted = False
        self.accepted_at = None
    
    def soft_delete(self) -> None:
        """Soft delete the invitation."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted invitation."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def get_expiry_days() -> int:
        """Get default expiry days."""
        return 7
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
