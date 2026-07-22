# ============================================================
# AETHER LINK - TEACHER INVITATION MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import re
from ..core.database import Base


class InvitationStatus(str, enum.Enum):  # NEW
    """Invitation status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"
    RESENT = "resent"


class TeacherInvitation(Base):
    __tablename__ = "teacher_invitations"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # INVITATION DETAILS
    # ============================================================
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # NEW: Message to teacher (custom message from admin)
    message = Column(Text, nullable=True)
    
    # ============================================================
    # COURSE ASSIGNMENT
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # INVITER
    # ============================================================
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # SECURE TOKEN
    # ============================================================
    token = Column(String(255), unique=True, index=True, nullable=False)
    
    # NEW: Token version (for invalidation)
    token_version = Column(Integer, default=1, nullable=False)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=InvitationStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # NEW: Keep accepted boolean for compatibility
    accepted = Column(Boolean, default=False, nullable=False, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Expired tracking
    expired_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Revoked tracking
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # ============================================================
    # NEW: RESEND TRACKING
    # ============================================================
    resend_count = Column(Integer, default=0, nullable=False)
    last_resend_at = Column(DateTime(timezone=True), nullable=True)
    max_resends = Column(Integer, default=5, nullable=False)  # Limit resends
    
    # ============================================================
    # NEW: ORIGINAL INVITATION (for resend tracking)
    # ============================================================
    original_invitation_id = Column(Integer, ForeignKey("teacher_invitations.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # EXPIRY
    # ============================================================
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # NEW: Expiry hours (configurable)
    expiry_hours = Column(Integer, default=24, nullable=False)
    
    # ============================================================
    # NEW: USER REFERENCE (when accepted)
    # ============================================================
    accepted_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # NEW: REMINDER TRACKING
    # ============================================================
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_count = Column(Integer, default=0, nullable=False)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: SECURITY METADATA
    # ============================================================
    ip_address = Column(String(100), nullable=True)  # IP of invitee when accepted
    user_agent = Column(Text, nullable=True)  # User agent when accepted
    
    # NEW: Device fingerprint
    device_id = Column(String(255), nullable=True)
    
    # NEW: Location info
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_teacher_invitations_email_status', 'email', 'status'),
        Index('ix_teacher_invitations_course_status', 'course_id', 'status'),
        Index('ix_teacher_invitations_token_status', 'token', 'status'),
        Index('ix_teacher_invitations_expires_status', 'expires_at', 'status'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    invited_by_user = relationship(
        "User",
        foreign_keys=[invited_by],
        uselist=False
    )
    
    # NEW: Course relationship
    course = relationship(
        "Course",
        back_populates="teacher_invitations",
        foreign_keys=[course_id]
    )
    
    # NEW: Accepted user relationship
    accepted_user = relationship(
        "User",
        foreign_keys=[accepted_user_id],
        uselist=False
    )
    
    # NEW: Revoked by user
    revoked_by_user = relationship(
        "User",
        foreign_keys=[revoked_by],
        uselist=False
    )
    
    # NEW: Original invitation (for resend chain)
    original_invitation = relationship(
        "TeacherInvitation",
        remote_side=[id],
        foreign_keys=[original_invitation_id],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<TeacherInvitation {self.email}>"
    
    def __str__(self) -> str:
        return f"Invitation for {self.full_name} ({self.email})"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is pending."""
        return self.status == InvitationStatus.PENDING.value and not self.is_expired
    
    @property
    def is_accepted(self) -> bool:
        """Check if invitation is accepted."""
        return self.status == InvitationStatus.ACCEPTED.value
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return self.status == InvitationStatus.EXPIRED.value or func.now() > self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        """Check if invitation is revoked."""
        return self.status == InvitationStatus.REVOKED.value
    
    @property
    def is_active(self) -> bool:
        """Check if invitation is active (pending and not expired)."""
        return self.is_pending
    
    @property
    def can_resend(self) -> bool:
        """Check if invitation can be resent."""
        return (
            self.status in [InvitationStatus.PENDING.value, InvitationStatus.EXPIRED.value]
            and self.resend_count < self.max_resends
            and self.deleted_at is None
        )
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiry."""
        if self.is_expired:
            return 0
        delta = self.expires_at - func.now()
        return max(0, delta.days)
    
    @property
    def hours_until_expiry(self) -> float:
        """Get hours until expiry."""
        if self.is_expired:
            return 0.0
        delta = self.expires_at - func.now()
        return max(0.0, delta.total_seconds() / 3600)
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "pending": "Pending",
            "accepted": "Accepted",
            "expired": "Expired",
            "revoked": "Revoked",
            "resent": "Resent",
        }
        return status_map.get(self.status, "Unknown")
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def accept(self, user_id: int, ip_address: str = None, user_agent: str = None, device_id: str = None) -> None:
        """
        Mark invitation as accepted.
        
        Args:
            user_id: ID of the user who accepted
            ip_address: IP address of the accept request
            user_agent: User agent of the accept request
            device_id: Device fingerprint
        """
        self.status = InvitationStatus.ACCEPTED.value
        self.accepted = True
        self.accepted_at = func.now()
        self.accepted_user_id = user_id
        
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        if device_id:
            self.device_id = device_id
        
        # Create course teacher assignment
        # This will be handled by a service or trigger
    
    def revoke(self, revoked_by: int, reason: str = None) -> None:
        """
        Revoke invitation.
        
        Args:
            revoked_by: ID of the user who revoked
            reason: Reason for revocation
        """
        self.status = InvitationStatus.REVOKED.value
        self.revoked_at = func.now()
        self.revoked_by = revoked_by
        if reason:
            self.revocation_reason = reason
    
    def expire(self) -> None:
        """Mark invitation as expired."""
        self.status = InvitationStatus.EXPIRED.value
        self.expired_at = func.now()
    
    def resend(self, new_token: str, expiry_hours: int = 24) -> None:
        """
        Resend invitation with new token.
        
        Args:
            new_token: New secure token
            expiry_hours: Expiry hours for new token
        """
        self.token = new_token
        self.token_version += 1
        self.expires_at = func.now() + func.interval(f'{expiry_hours} hours')
        self.expiry_hours = expiry_hours
        
        # Reset status if expired
        if self.status == InvitationStatus.EXPIRED.value:
            self.status = InvitationStatus.PENDING.value
            self.expired_at = None
        
        # Track resend
        self.resend_count += 1
        self.last_resend_at = func.now()
        self.status = InvitationStatus.RESENT.value  # Track that it was resent
        # Then set back to pending for active use
        # We'll handle this in service
    
    def mark_resent(self) -> None:
        """Mark invitation as resent (for tracking)."""
        self.resend_count += 1
        self.last_resend_at = func.now()
    
    def send_reminder(self) -> None:
        """Record that a reminder was sent."""
        self.reminder_sent_at = func.now()
        self.reminder_count += 1
        self.last_reminder_at = func.now()
    
    def can_send_reminder(self) -> bool:
        """Check if a reminder can be sent."""
        if self.reminder_count >= 3:  # Max 3 reminders
            return False
        if self.last_reminder_at:
            # Wait at least 24 hours between reminders
            delta = func.now() - self.last_reminder_at
            if delta.total_seconds() < 86400:
                return False
        return self.is_pending
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def set_location(self, country: str, city: str) -> None:
        """Set location information."""
        self.country = country
        self.city = city
    
    def soft_delete(self) -> None:
        """Soft delete the invitation."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted invitation."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_full_name(name: str) -> bool:
        """Validate full name."""
        return 2 <= len(name) <= 255
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert invitation to dictionary."""
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "course_id": self.course_id,
            "course_title": self.course.title if self.course else None,
            "status": self.status,
            "display_status": self.display_status,
            "is_pending": self.is_pending,
            "is_accepted": self.is_accepted,
            "is_expired": self.is_expired,
            "is_revoked": self.is_revoked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "days_until_expiry": self.days_until_expiry,
            "hours_until_expiry": self.hours_until_expiry,
            "resend_count": self.resend_count,
            "can_resend": self.can_resend,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "accepted_user_id": self.accepted_user_id,
        }
        
        if include_sensitive:
            data.update({
                "token": self.token,  # Only for admin use
                "token_version": self.token_version,
                "message": self.message,
                "expiry_hours": self.expiry_hours,
                "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
                "revoked_by": self.revoked_by,
                "revocation_reason": self.revocation_reason,
                "expired_at": self.expired_at.isoformat() if self.expired_at else None,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "device_id": self.device_id,
                "country": self.country,
                "city": self.city,
                "reminder_sent_at": self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
                "reminder_count": self.reminder_count,
                "last_reminder_at": self.last_reminder_at.isoformat() if self.last_reminder_at else None,
                "original_invitation_id": self.original_invitation_id,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing invitation data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("token", None)
        data.pop("message", None)
        data.pop("ip_address", None)
        data.pop("user_agent", None)
        data.pop("device_id", None)
        data.pop("country", None)
        data.pop("city", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing invitation data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: TEACHER INVITATION AUDIT LOG
# ============================================================

class TeacherInvitationAuditLog(Base):
    """Track all teacher invitation events for auditing."""
    __tablename__ = "teacher_invitation_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    invitation_id = Column(Integer, ForeignKey("teacher_invitations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event type
    event_type = Column(String(50), nullable=False)  # created, resent, accepted, expired, revoked, reminder_sent
    
    # Action details
    action_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Details
    details = Column(JSON, nullable=True)
    
    # Relationships
    invitation = relationship("TeacherInvitation", foreign_keys=[invitation_id])
    actor = relationship("User", foreign_keys=[action_by])
    
    def __repr__(self) -> str:
        return f"<TeacherInvitationAuditLog {self.id}: {self.event_type}>"