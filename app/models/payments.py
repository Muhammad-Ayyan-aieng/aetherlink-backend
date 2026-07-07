# ============================================================
# AETHER LINK - PAYMENT MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, DECIMAL, Text, Index
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"


class Payment(Base):
    __tablename__ = "payments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False, unique=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ============================================================
    # PAYMENT DETAILS
    # ============================================================
    amount = Column(DECIMAL(10, 2), nullable=False)
    method = Column(
        SQLEnum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        default=PaymentMethod.EASYPAISA,
        nullable=False
    )
    status = Column(
        SQLEnum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    
    # ============================================================
    # EASY PAISA / JAZZCASH FIELDS
    # ============================================================
    easypaisa_account = Column(String(50), default="03XX-XXXXXXX", nullable=True)
    easypaisa_holder = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    sender_phone = Column(String(20), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    
    # ============================================================
    # SCREENSHOT
    # ============================================================
    screenshot_url = Column(String(500), nullable=True)
    screenshot_uploaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # ============================================================
    # REJECTION
    # ============================================================
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # ============================================================
    # REFUND
    # ============================================================
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    refund_reason = Column(Text, nullable=True)
    refund_processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # ============================================================
    # METADATA (Security)
    # ============================================================
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
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
        Index('ix_payments_enrollment', 'enrollment_id', unique=True),
        Index('ix_payments_transaction', 'transaction_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment = relationship(
        "Enrollment",
        back_populates="payment",
        foreign_keys=[enrollment_id],
        uselist=False
    )
    
    student = relationship(
        "User",
        back_populates="payments",
        foreign_keys=[student_id]
    )
    
    verified_by_user = relationship(
        "User",
        back_populates="verified_payments",
        foreign_keys=[verified_by]
    )
    
    refund_processed_by_user = relationship(
        "User",
        foreign_keys=[refund_processed_by]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Payment {self.id}: {self.amount} - {self.status}>"
    
    def __str__(self) -> str:
        return f"Payment #{self.id} - {self.student.full_name} - {self.amount} PKR"
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status == PaymentStatus.PENDING
    
    @property
    def is_awaiting_verification(self) -> bool:
        """Check if payment is awaiting verification."""
        return self.status == PaymentStatus.AWAITING_VERIFICATION
    
    @property
    def is_verified(self) -> bool:
        """Check if payment is verified."""
        return self.status == PaymentStatus.VERIFIED
    
    @property
    def is_rejected(self) -> bool:
        """Check if payment is rejected."""
        return self.status == PaymentStatus.REJECTED
    
    @property
    def is_refunded(self) -> bool:
        """Check if payment is refunded."""
        return self.status == PaymentStatus.REFUNDED
    
    @property
    def has_screenshot(self) -> bool:
        """Check if screenshot is uploaded."""
        return self.screenshot_url is not None
    
    def upload_screenshot(self, url: str) -> None:
        """Upload payment screenshot."""
        self.screenshot_url = url
        self.screenshot_uploaded_at = func.now()
        self.status = PaymentStatus.AWAITING_VERIFICATION
    
    def verify(self, verified_by: int, notes: str = None) -> None:
        """Verify payment."""
        self.status = PaymentStatus.VERIFIED
        self.verified_by = verified_by
        self.verified_at = func.now()
        if notes:
            self.verification_notes = notes
        # Activate enrollment
        if self.enrollment:
            self.enrollment.activate(verified_by)
    
    def reject(self, verified_by: int, reason: str) -> None:
        """Reject payment."""
        self.status = PaymentStatus.REJECTED
        self.verified_by = verified_by
        self.rejected_at = func.now()
        self.rejection_reason = reason
        # Cancel enrollment
        if self.enrollment:
            self.enrollment.cancel()
    
    def refund(self, processed_by: int, reason: str = None) -> None:
        """Refund payment."""
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = func.now()
        self.refund_processed_by = processed_by
        if reason:
            self.refund_reason = reason
        # Cancel enrollment
        if self.enrollment:
            self.enrollment.cancel()
    
    def add_transaction(self, transaction_id: str) -> None:
        """Add transaction ID from Easy Paisa."""
        self.transaction_id = transaction_id
    
    def add_sender(self, name: str, phone: str) -> None:
        """Add sender details from Easy Paisa."""
        self.sender_name = name
        self.sender_phone = phone
    
    def soft_delete(self) -> None:
        """Soft delete the payment."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted payment."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def validate_amount(amount: float) -> bool:
        """Validate payment amount."""
        return 0 <= amount <= 999999
    
    @staticmethod
    def validate_transaction_id(transaction_id: str) -> bool:
        """Validate transaction ID format."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9\-_]+$', transaction_id)) if transaction_id else True