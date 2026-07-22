# ============================================================
# AETHER LINK - ENROLLMENT MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, DECIMAL, Text, Index, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class EnrollmentStatus(str, enum.Enum):
    """Enrollment status enumeration."""
    PENDING = "pending"
    PAYMENT_VERIFICATION = "payment_verification"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"


class EnrollmentSource(str, enum.Enum):  # NEW
    """Source of enrollment."""
    DIRECT = "direct"  # Student applied directly
    LEARNING_PATH = "learning_path"  # Via learning path
    COUPON = "coupon"  # Via coupon/discount
    ADMIN = "admin"  # Admin enrolled the student
    UPGRADE = "upgrade"  # Upgraded from another enrollment


class Enrollment(Base):
    __tablename__ = "enrollments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        SQLEnum(EnrollmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=EnrollmentStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # PAYMENT
    # ============================================================
    payment_amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(
        SQLEnum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        default=PaymentMethod.EASYPAISA,
        nullable=False
    )
    payment_screenshot = Column(String(500), nullable=True)
    
    # NEW: Payment transaction ID (for tracking)
    payment_transaction_id = Column(String(100), nullable=True, index=True)
    
    # ============================================================
    # PAYMENT VERIFICATION
    # ============================================================
    payment_verified = Column(Boolean, default=False, nullable=False, index=True)
    payment_verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    payment_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Payment rejection tracking
    payment_rejection_reason = Column(Text, nullable=True)
    payment_rejected_at = Column(DateTime(timezone=True), nullable=True)
    payment_rejected_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # DATES
    # ============================================================
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Last accessed timestamp (for engagement tracking)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # PROGRESS
    # ============================================================
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # NEW: Detailed progress tracking
    completed_sessions = Column(Integer, default=0, nullable=False)
    total_sessions = Column(Integer, default=0, nullable=False)  # Cached from course
    completed_materials = Column(Integer, default=0, nullable=False)
    total_materials = Column(Integer, default=0, nullable=False)  # Cached from course
    
    # NEW: Time tracking
    total_time_spent_minutes = Column(Integer, default=0, nullable=False)
    last_session_time = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: ENROLLMENT SOURCE & METADATA
    # ============================================================
    source = Column(
        String(50),
        default=EnrollmentSource.DIRECT.value,
        nullable=False,
        index=True
    )
    
    # NEW: Reference IDs (for learning path, coupon, etc.)
    source_reference_id = Column(Integer, nullable=True, index=True)  # path_id, coupon_id, etc.
    source_reference_type = Column(String(50), nullable=True)  # 'learning_path', 'coupon', etc.
    
    # NEW: Discount information
    discount_applied = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    discount_type = Column(String(20), nullable=True)  # 'percentage', 'fixed'
    discount_value = Column(DECIMAL(10, 2), nullable=True)
    coupon_code = Column(String(50), nullable=True)
    
    # ============================================================
    # NEW: CERTIFICATE TRACKING
    # ============================================================
    certificate_issued = Column(Boolean, default=False, nullable=False)
    certificate_issued_at = Column(DateTime(timezone=True), nullable=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # NOTES
    # ============================================================
    notes = Column(Text, nullable=True)
    
    # NEW: Internal notes (admin only)
    admin_notes = Column(Text, nullable=True)
    
    # NEW: Student feedback (after completion)
    student_feedback = Column(Text, nullable=True)
    student_rating = Column(Integer, nullable=True)  # 1-5
    
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
        Index('ix_enrollments_unique', 'student_id', 'course_id', unique=True),
        Index('ix_enrollments_student_active', 'student_id', 'status'),  # NEW
        Index('ix_enrollments_course_status', 'course_id', 'status'),  # NEW
        Index('ix_enrollments_progress', 'progress_percentage'),  # NEW
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    student = relationship(
        "User",
        back_populates="enrollments",
        foreign_keys=[student_id]
    )
    
    course = relationship(
        "Course",
        back_populates="enrollments",
        foreign_keys=[course_id]
    )
    
    verified_by_user = relationship(
        "User",
        back_populates="verified_enrollments",
        foreign_keys=[payment_verified_by]
    )
    
    # NEW: Rejected by user
    rejected_by_user = relationship(
        "User",
        foreign_keys=[payment_rejected_by],
        uselist=False
    )
    
    attendance_records = relationship(
        "Attendance",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    
    payment = relationship(
        "Payment",
        back_populates="enrollment",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # NEW: Certificate relationship
    certificate = relationship(
        "Certificate",
        foreign_keys=[certificate_id],
        uselist=False
    )
    
    # NEW: Assignment submissions
    assignment_submissions = relationship(
        "AssignmentSubmission",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    
    # NEW: Coupon usage
    coupon_usage = relationship(
        "CouponUsage",
        back_populates="enrollment",
        uselist=False
    )
    
    # NEW: Path enrollment (if from learning path)
    path_enrollment = relationship(
        "PathEnrollment",
        foreign_keys=[source_reference_id],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Enrollment {self.id}: {self.student_id} -> {self.course_id}>"
    
    def __str__(self) -> str:
        return f"{self.student.full_name} -> {self.course.title}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_pending(self) -> bool:
        """Check if enrollment is pending."""
        return self.status == EnrollmentStatus.PENDING
    
    @property
    def is_payment_verification(self) -> bool:
        """Check if enrollment is in payment verification."""
        return self.status == EnrollmentStatus.PAYMENT_VERIFICATION
    
    @property
    def is_active(self) -> bool:
        """Check if enrollment is active."""
        return self.status == EnrollmentStatus.ACTIVE
    
    @property
    def is_completed(self) -> bool:
        """Check if enrollment is completed."""
        return self.status == EnrollmentStatus.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if enrollment is cancelled."""
        return self.status == EnrollmentStatus.CANCELLED
    
    @property
    def is_expired(self) -> bool:
        """Check if enrollment is expired."""
        return self.status == EnrollmentStatus.EXPIRED
    
    @property
    def is_payment_verified(self) -> bool:
        """Check if payment is verified."""
        return self.payment_verified
    
    @property
    def is_progress_complete(self) -> bool:
        """Check if progress is 100%."""
        return self.progress_percentage >= 100
    
    @property
    def is_fully_completed(self) -> bool:
        """Check if enrollment is fully completed (progress 100% and status completed)."""
        return self.is_progress_complete and self.is_completed
    
    @property
    def is_has_certificate(self) -> bool:
        """Check if certificate has been issued."""
        return self.certificate_issued
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiry."""
        if self.expires_at is None:
            return -1
        delta = self.expires_at - func.now()
        return max(0, delta.days)
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if enrollment is expiring soon (within 7 days)."""
        if self.expires_at is None:
            return False
        return 0 < self.days_until_expiry <= 7
    
    @property
    def has_discount(self) -> bool:
        """Check if discount was applied."""
        return self.discount_applied > 0
    
    @property
    def effective_paid_amount(self) -> float:
        """Get effective paid amount after discount."""
        return float(self.payment_amount) - float(self.discount_applied)
    
    @property
    def engagement_score(self) -> float:
        """Calculate engagement score (0-100)."""
        if self.total_sessions == 0:
            return 0.0
        session_score = (self.completed_sessions / self.total_sessions) * 50
        material_score = (self.completed_materials / self.total_materials) * 50 if self.total_materials > 0 else 0
        return session_score + material_score
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def activate(self, verified_by: int, notes: str = None) -> None:
        """
        Activate enrollment after payment verification.
        
        Args:
            verified_by: Admin ID who verified the payment
            notes: Additional notes about verification
        """
        self.status = EnrollmentStatus.ACTIVE
        self.payment_verified = True
        self.payment_verified_by = verified_by
        self.payment_verified_at = func.now()
        
        # Set expiry 90 days from now (configurable via settings)
        self.expires_at = func.now() + func.interval('90 days')
        
        if notes:
            self.notes = notes
    
    def reject_payment(self, rejected_by: int, reason: str) -> None:
        """
        Reject payment and cancel enrollment.
        
        Args:
            rejected_by: Admin ID who rejected the payment
            reason: Reason for rejection
        """
        self.status = EnrollmentStatus.CANCELLED
        self.payment_verified = False
        self.payment_rejected_at = func.now()
        self.payment_rejected_by = rejected_by
        self.payment_rejection_reason = reason
    
    def complete(self) -> None:
        """Mark enrollment as completed."""
        self.status = EnrollmentStatus.COMPLETED
        self.completed_at = func.now()
        self.progress_percentage = 100
    
    def cancel(self, reason: str = None) -> None:
        """Cancel enrollment."""
        self.status = EnrollmentStatus.CANCELLED
        if reason:
            self.notes = reason
    
    def expire(self) -> None:
        """Expire enrollment."""
        self.status = EnrollmentStatus.EXPIRED
    
    def update_progress(self, progress: int) -> None:
        """
        Update progress percentage.
        Ensures progress is between 0 and 100.
        """
        if progress < 0:
            progress = 0
        elif progress > 100:
            progress = 100
        
        self.progress_percentage = progress
        
        # If progress is 100% and status is active, auto-complete
        if self.progress_percentage >= 100 and self.status == EnrollmentStatus.ACTIVE:
            self.complete()
    
    def update_engagement(self, time_spent_minutes: int = 0) -> None:
        """Update engagement metrics."""
        self.last_accessed_at = func.now()
        if time_spent_minutes > 0:
            self.total_time_spent_minutes += time_spent_minutes
    
    def mark_session_completed(self, session_count: int = 1) -> None:
        """Mark sessions as completed."""
        self.completed_sessions += session_count
        self.last_session_time = func.now()
        
        # Recalculate progress
        if self.total_sessions > 0:
            progress = min(100, int((self.completed_sessions / self.total_sessions) * 100))
            self.update_progress(progress)
    
    def mark_material_completed(self, material_count: int = 1) -> None:
        """Mark materials as completed."""
        self.completed_materials += material_count
    
    def issue_certificate(self, certificate_id: int) -> None:
        """
        Issue certificate for this enrollment.
        
        Args:
            certificate_id: ID of the issued certificate
        """
        self.certificate_issued = True
        self.certificate_issued_at = func.now()
        self.certificate_id = certificate_id
    
    def set_discount(self, coupon_code: str, discount_amount: float, discount_type: str, discount_value: float) -> None:
        """Apply discount to enrollment."""
        self.coupon_code = coupon_code
        self.discount_applied = discount_amount
        self.discount_type = discount_type
        self.discount_value = discount_value
    
    def set_source(self, source: str, reference_id: int = None, reference_type: str = None) -> None:
        """Set enrollment source."""
        self.source = source
        self.source_reference_id = reference_id
        self.source_reference_type = reference_type
    
    def soft_delete(self) -> None:
        """Soft delete the enrollment."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted enrollment."""
        self.deleted_at = None
    
    def add_student_feedback(self, rating: int, feedback: str) -> None:
        """Add student feedback after course completion."""
        self.student_rating = max(1, min(5, rating))
        self.student_feedback = feedback
    
    def add_admin_note(self, note: str) -> None:
        """Add admin-only note."""
        if self.admin_notes:
            self.admin_notes += f"\n{func.now()}: {note}"
        else:
            self.admin_notes = f"{func.now()}: {note}"
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_progress(progress: int) -> bool:
        """Validate progress is within limits."""
        return 0 <= progress <= 100
    
    @staticmethod
    def validate_payment_amount(amount: float) -> bool:
        """Validate payment amount."""
        return amount >= 0
    
    @staticmethod
    def validate_rating(rating: int) -> bool:
        """Validate rating is within limits."""
        return 1 <= rating <= 5
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert enrollment to dictionary."""
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "course_title": self.course.title if self.course else None,
            "student_name": self.student.full_name if self.student else None,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "payment_amount": float(self.payment_amount),
            "payment_method": self.payment_method.value if self.payment_method else None,
            "payment_verified": self.payment_verified,
            "discount_applied": float(self.discount_applied) if self.discount_applied else 0.0,
            "effective_paid_amount": self.effective_paid_amount,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percentage": self.progress_percentage,
            "completed_sessions": self.completed_sessions,
            "total_sessions": self.total_sessions,
            "engagement_score": self.engagement_score,
            "total_time_spent_minutes": self.total_time_spent_minutes,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "certificate_issued": self.certificate_issued,
            "source": self.source,
            "has_discount": self.has_discount,
            "days_until_expiry": self.days_until_expiry,
            "is_expiring_soon": self.is_expiring_soon,
        }
        
        if include_sensitive:
            data.update({
                "payment_transaction_id": self.payment_transaction_id,
                "payment_screenshot": self.payment_screenshot,
                "payment_verified_by": self.payment_verified_by,
                "payment_verified_at": self.payment_verified_at.isoformat() if self.payment_verified_at else None,
                "payment_rejected_at": self.payment_rejected_at.isoformat() if self.payment_rejected_at else None,
                "payment_rejection_reason": self.payment_rejection_reason,
                "coupon_code": self.coupon_code,
                "discount_type": self.discount_type,
                "discount_value": float(self.discount_value) if self.discount_value else None,
                "source_reference_id": self.source_reference_id,
                "source_reference_type": self.source_reference_type,
                "certificate_id": self.certificate_id,
                "certificate_issued_at": self.certificate_issued_at.isoformat() if self.certificate_issued_at else None,
                "student_rating": self.student_rating,
                "student_feedback": self.student_feedback,
                "admin_notes": self.admin_notes,
                "notes": self.notes,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing enrollment data (safe for API responses)."""
        data = self.to_dict()
        # Remove internal fields for public view
        data.pop("payment_transaction_id", None)
        data.pop("payment_screenshot", None)
        data.pop("payment_rejection_reason", None)
        data.pop("coupon_code", None)
        data.pop("admin_notes", None)
        data.pop("metadata", None)
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing enrollment data."""
        data = self.to_public_json()
        # Include student-specific fields
        data.update({
            "can_access": self.is_active and not self.is_expired,
            "has_certificate": self.certificate_issued,
            "certificate_url": f"/api/v1/certificates/{self.certificate_id}" if self.certificate_id else None,
        })
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing enrollment data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: ENROLLMENT HISTORY LOG (Audit Trail)
# ============================================================

class EnrollmentHistory(Base):
    """Track enrollment status changes for auditing."""
    __tablename__ = "enrollment_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status change
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    
    # Action details
    action = Column(String(50), nullable=False)  # 'created', 'activated', 'completed', 'cancelled', 'expired'
    action_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    
    # Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    enrollment = relationship("Enrollment")
    actor = relationship("User", foreign_keys=[action_by])
    
    def __repr__(self) -> str:
        return f"<EnrollmentHistory {self.id}: {self.from_status} -> {self.to_status}>"