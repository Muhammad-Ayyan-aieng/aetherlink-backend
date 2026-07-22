# ============================================================
# AETHER LINK - APPLICATION MODEL (UPGRADED)
# ============================================================

from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class ApplicationStatus(str, enum.Enum):
    """Application status enumeration."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"  # NEW: Admin is reviewing
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"  # NEW: Student withdrew


class ApplicationSource(str, enum.Enum):  # NEW
    """Application source enumeration."""
    WEBSITE = "website"
    LANDING_PAGE = "landing_page"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


class ApplicationPriority(str, enum.Enum):  # NEW
    """Application priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Application(Base):
    __tablename__ = "applications"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)

    # ============================================================
    # APPLICANT INFORMATION
    # ============================================================
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # NEW: Applicant details
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # NEW: Education/Background
    education = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=True)
    year_of_graduation = Column(Integer, nullable=True)
    experience_years = Column(Integer, nullable=True)
    current_occupation = Column(String(255), nullable=True)

    # ============================================================
    # COURSE
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)

    # ============================================================
    # APPLICATION DETAILS
    # ============================================================
    message = Column(Text, nullable=True)
    status = Column(
        SQLEnum(ApplicationStatus, values_callable=lambda x: [e.value for e in x]),
        default=ApplicationStatus.PENDING,
        nullable=False,
        index=True
    )
    admin_notes = Column(Text, nullable=True)
    
    # NEW: Priority
    priority = Column(
        String(20),
        default=ApplicationPriority.NORMAL.value,
        nullable=False
    )
    
    # NEW: Source
    source = Column(
        String(50),
        default=ApplicationSource.WEBSITE.value,
        nullable=False
    )
    
    # NEW: How did they hear about us?
    referral_source = Column(String(255), nullable=True)
    
    # NEW: Expected start date
    expected_start_date = Column(DateTime(timezone=True), nullable=True)

    # ============================================================
    # APPROVAL/REJECTION
    # ============================================================
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # NEW: Review tracking
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Withdrawal tracking
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    withdrawal_reason = Column(Text, nullable=True)

    # ============================================================
    # NEW: FOLLOW-UP TRACKING
    # ============================================================
    follow_up_notes = Column(Text, nullable=True)
    last_follow_up_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_count = Column(Integer, default=0, nullable=False)
    next_follow_up_at = Column(DateTime(timezone=True), nullable=True)

    # ============================================================
    # NEW: CONVERSION TRACKING
    # ============================================================
    converted_to_enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True, index=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: IP & TRACKING
    # ============================================================
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    
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
        Index('ix_applications_course_status', 'course_id', 'status'),
        Index('ix_applications_email_status', 'email', 'status'),
        Index('ix_applications_priority', 'priority'),
        Index('ix_applications_source', 'source'),
    )

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship("Course", foreign_keys=[course_id])
    approver = relationship("User", foreign_keys=[approved_by])
    
    # NEW: Rejected by user
    rejected_by_user = relationship("User", foreign_keys=[rejected_by], uselist=False)
    
    # NEW: Reviewed by user
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by], uselist=False)
    
    # NEW: Withdrawn by user
    withdrawn_by_user = relationship("User", foreign_keys=[withdrawn_by], uselist=False)
    
    # NEW: Converted enrollment
    converted_enrollment = relationship("Enrollment", foreign_keys=[converted_to_enrollment_id], uselist=False)

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        return f"<Application {self.email} - {self.status}>"

    def __str__(self) -> str:
        return f"{self.full_name} - {self.email}"

    # ============================================================
    # PROPERTIES
    # ============================================================

    @property
    def is_pending(self) -> bool:
        """Check if application is pending."""
        return self.status == ApplicationStatus.PENDING
    
    @property
    def is_under_review(self) -> bool:
        """Check if application is under review."""
        return self.status == ApplicationStatus.UNDER_REVIEW
    
    @property
    def is_approved(self) -> bool:
        """Check if application is approved."""
        return self.status == ApplicationStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        """Check if application is rejected."""
        return self.status == ApplicationStatus.REJECTED
    
    @property
    def is_withdrawn(self) -> bool:
        """Check if application is withdrawn."""
        return self.status == ApplicationStatus.WITHDRAWN
    
    @property
    def is_high_priority(self) -> bool:
        """Check if application is high priority."""
        return self.priority in [ApplicationPriority.HIGH.value, ApplicationPriority.URGENT.value]
    
    @property
    def is_converted(self) -> bool:
        """Check if application was converted to enrollment."""
        return self.converted_to_enrollment_id is not None
    
    @property
    def days_pending(self) -> int:
        """Get days since application was created."""
        if self.created_at is None:
            return 0
        delta = func.now() - self.created_at
        return delta.days
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "pending": "Pending Review",
            "under_review": "Under Review",
            "approved": "Approved",
            "rejected": "Rejected",
            "withdrawn": "Withdrawn",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def display_priority(self) -> str:
        """Get human-readable priority."""
        priority_map = {
            "low": "Low",
            "normal": "Normal",
            "high": "High",
            "urgent": "Urgent",
        }
        return priority_map.get(self.priority, "Normal")
    
    @property
    def display_source(self) -> str:
        """Get human-readable source."""
        source_map = {
            "website": "Website",
            "landing_page": "Landing Page",
            "referral": "Referral",
            "social_media": "Social Media",
            "other": "Other",
        }
        return source_map.get(self.source, "Website")

    # ============================================================
    # METHODS
    # ============================================================

    def approve(self, admin_id: int, notes: Optional[str] = None) -> None:
        """
        Approve the application and create enrollment.
        
        Args:
            admin_id: ID of admin approving
            notes: Optional admin notes
        """
        self.status = ApplicationStatus.APPROVED
        self.approved_by = admin_id
        self.approved_at = func.now()
        if notes:
            self.admin_notes = notes
    
    def reject(self, admin_id: int, reason: str) -> None:
        """
        Reject the application.
        
        Args:
            admin_id: ID of admin rejecting
            reason: Reason for rejection
        """
        self.status = ApplicationStatus.REJECTED
        self.rejected_by = admin_id
        self.rejected_at = func.now()
        self.admin_notes = reason
    
    def mark_under_review(self, admin_id: int) -> None:
        """
        Mark application as under review.
        
        Args:
            admin_id: ID of admin reviewing
        """
        self.status = ApplicationStatus.UNDER_REVIEW
        self.reviewed_by = admin_id
        self.reviewed_at = func.now()
    
    def withdraw(self, reason: Optional[str] = None) -> None:
        """
        Withdraw the application.
        
        Args:
            reason: Reason for withdrawal
        """
        self.status = ApplicationStatus.WITHDRAWN
        self.withdrawn_at = func.now()
        if reason:
            self.withdrawal_reason = reason
    
    def mark_converted(self, enrollment_id: int) -> None:
        """
        Mark application as converted to enrollment.
        
        Args:
            enrollment_id: ID of the created enrollment
        """
        self.converted_to_enrollment_id = enrollment_id
        self.converted_at = func.now()
    
    def record_follow_up(self, notes: str) -> None:
        """Record a follow-up action."""
        self.follow_up_count += 1
        self.last_follow_up_at = func.now()
        self.follow_up_notes = notes
    
    def schedule_follow_up(self, follow_up_date: DateTime) -> None:
        """Schedule a follow-up."""
        self.next_follow_up_at = follow_up_date
    
    def set_priority(self, priority: str) -> None:
        """Set application priority."""
        if priority in [p.value for p in ApplicationPriority]:
            self.priority = priority
    
    def set_source(self, source: str, referral: Optional[str] = None) -> None:
        """Set application source."""
        if source in [s.value for s in ApplicationSource]:
            self.source = source
        if referral:
            self.referral_source = referral
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete(self) -> None:
        """Soft delete the application."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted application."""
        self.deleted_at = None

    # ============================================================
    # VALIDATION METHODS
    # ============================================================

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number."""
        if not phone:
            return True
        import re
        pattern = r'^[0-9+\-\(\) ]+$'
        return bool(re.match(pattern, phone))

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert application to dictionary."""
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "course_id": self.course_id,
            "course_title": self.course.title if self.course else None,
            "message": self.message,
            "status": self.status.value if self.status else None,
            "display_status": self.display_status,
            "priority": self.priority,
            "display_priority": self.display_priority,
            "source": self.source,
            "display_source": self.display_source,
            "is_pending": self.is_pending,
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
            "is_high_priority": self.is_high_priority,
            "is_converted": self.is_converted,
            "days_pending": self.days_pending,
            "education": self.education,
            "institution": self.institution,
            "experience_years": self.experience_years,
            "current_occupation": self.current_occupation,
            "follow_up_count": self.follow_up_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
        }
        
        if include_sensitive:
            data.update({
                "address": self.address,
                "city": self.city,
                "country": self.country,
                "postal_code": self.postal_code,
                "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
                "year_of_graduation": self.year_of_graduation,
                "expected_start_date": self.expected_start_date.isoformat() if self.expected_start_date else None,
                "referral_source": self.referral_source,
                "admin_notes": self.admin_notes,
                "follow_up_notes": self.follow_up_notes,
                "last_follow_up_at": self.last_follow_up_at.isoformat() if self.last_follow_up_at else None,
                "next_follow_up_at": self.next_follow_up_at.isoformat() if self.next_follow_up_at else None,
                "converted_to_enrollment_id": self.converted_to_enrollment_id,
                "converted_at": self.converted_at.isoformat() if self.converted_at else None,
                "approved_by": self.approved_by,
                "rejected_by": self.rejected_by,
                "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
                "reviewed_by": self.reviewed_by,
                "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
                "withdrawn_at": self.withdrawn_at.isoformat() if self.withdrawn_at else None,
                "withdrawal_reason": self.withdrawal_reason,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "device_type": self.device_type,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing application data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("address", None)
        data.pop("city", None)
        data.pop("country", None)
        data.pop("postal_code", None)
        data.pop("date_of_birth", None)
        data.pop("phone", None)
        data.pop("message", None)
        data.pop("ip_address", None)
        data.pop("user_agent", None)
        data.pop("device_type", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing application data (full access)."""
        return self.to_dict(include_sensitive=True)