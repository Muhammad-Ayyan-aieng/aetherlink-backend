# ============================================================
# AETHER LINK - ENROLLMENT MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, DECIMAL, Text, Index
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


class Enrollment(Base):
    __tablename__ = "enrollments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        SQLEnum(EnrollmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=EnrollmentStatus.PENDING,
        nullable=False
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
    
    # ============================================================
    # PAYMENT VERIFICATION
    # ============================================================
    payment_verified = Column(Boolean, default=False, nullable=False)
    payment_verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    payment_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # DATES
    # ============================================================
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # PROGRESS
    # ============================================================
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # NOTES
    # ============================================================
    notes = Column(Text, nullable=True)
    
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
        # Prevent duplicate enrollments
        Index('ix_enrollments_unique', 'student_id', 'course_id', unique=True),
        # Ensure progress is between 0 and 100
        Index('ix_enrollments_progress_check'),
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
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Enrollment {self.id}: {self.student_id} -> {self.course_id}>"
    
    def __str__(self) -> str:
        return f"{self.student.full_name} -> {self.course.title}"
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    @property
    def is_pending(self) -> bool:
        """Check if enrollment is pending."""
        return self.status == EnrollmentStatus.PENDING
    
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
    
    def activate(self, verified_by: int) -> None:
        """
        Activate enrollment after payment verification.
        """
        self.status = EnrollmentStatus.ACTIVE
        self.payment_verified = True
        self.payment_verified_by = verified_by
        self.payment_verified_at = func.now()
        # Set expiry 90 days from now
        self.expires_at = func.now() + func.interval('90 days')
    
    def complete(self) -> None:
        """Mark enrollment as completed."""
        self.status = EnrollmentStatus.COMPLETED
        self.completed_at = func.now()
        self.progress_percentage = 100
    
    def cancel(self) -> None:
        """Cancel enrollment."""
        self.status = EnrollmentStatus.CANCELLED
    
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
        
        # If progress is 100%, auto-complete
        if self.progress_percentage >= 100 and self.status == EnrollmentStatus.ACTIVE:
            self.complete()
    
    def soft_delete(self) -> None:
        """Soft delete the enrollment."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted enrollment."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION (Future - used in schemas)
    # ============================================================
    
    @staticmethod
    def validate_progress(progress: int) -> bool:
        """Validate progress is within limits."""
        return 0 <= progress <= 100
    
    @staticmethod
    def validate_payment_amount(amount: float) -> bool:
        """Validate payment amount."""
        return amount >= 0
