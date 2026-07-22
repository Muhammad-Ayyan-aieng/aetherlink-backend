# ============================================================
# AETHER LINK - PAYMENT MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, DECIMAL, Text, Index, JSON, BigInteger
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import re
from ..core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    FAILED = "failed"  # NEW: For failed payment attempts
    CANCELLED = "cancelled"  # NEW: For cancelled payments


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"
    CARD = "card"  # NEW: Credit/debit card
    CRYPTO = "crypto"  # NEW: Cryptocurrency


class PaymentGateway(str, enum.Enum):  # NEW
    """Payment gateway enumeration."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    PAYPAL = "paypal"
    NONE = "none"  # Manual payment


class PaymentType(str, enum.Enum):  # NEW
    """Payment type enumeration."""
    COURSE_FEE = "course_fee"
    SUBSCRIPTION = "subscription"
    INVOICE = "invoice"
    REFUND = "refund"


class Payment(Base):
    __tablename__ = "payments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True, unique=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
        nullable=False,
        index=True
    )
    
    # NEW: Payment type
    payment_type = Column(
        String(50),
        default=PaymentType.COURSE_FEE.value,
        nullable=False
    )
    
    # NEW: Gateway information
    gateway = Column(
        String(50),
        default=PaymentGateway.NONE.value,
        nullable=False
    )
    
    # NEW: Gateway transaction ID (from payment gateway)
    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    gateway_response = Column(JSON, nullable=True)  # Raw gateway response
    
    # ============================================================
    # EASY PAISA / JAZZCASH FIELDS
    # ============================================================
    easypaisa_account = Column(String(50), nullable=True)
    easypaisa_holder = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    sender_phone = Column(String(20), nullable=True)
    transaction_id = Column(String(100), nullable=True, index=True)
    
    # ============================================================
    # SCREENSHOT
    # ============================================================
    screenshot_url = Column(String(500), nullable=True)
    screenshot_uploaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Screenshot metadata
    screenshot_file_size = Column(Integer, nullable=True)  # In bytes
    screenshot_mime_type = Column(String(50), nullable=True)
    
    # ============================================================
    # NEW: PAYMENT INTENT (For future API integration)
    # ============================================================
    payment_intent_id = Column(String(255), nullable=True, index=True)
    payment_intent_secret = Column(String(255), nullable=True)  # Client secret
    
    # ============================================================
    # NEW: SUBSCRIPTION (For recurring payments)
    # ============================================================
    subscription_id = Column(String(255), nullable=True, index=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_interval = Column(String(50), nullable=True)  # monthly, yearly
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    subscription_cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # NEW: Verification method
    verification_method = Column(String(50), nullable=True)  # manual, api, webhook
    
    # ============================================================
    # REJECTION
    # ============================================================
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # REFUND
    # ============================================================
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    refund_reason = Column(Text, nullable=True)
    refund_processed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # NEW: Refund amount (could be partial)
    refund_amount = Column(DECIMAL(10, 2), nullable=True)
    refund_transaction_id = Column(String(255), nullable=True)
    refund_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: RETRY TRACKING
    # ============================================================
    retry_count = Column(Integer, default=0, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # SECURITY METADATA
    # ============================================================
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # NEW: Device fingerprint
    device_id = Column(String(255), nullable=True)
    
    # NEW: Session ID (for tracking)
    session_id = Column(String(255), nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_payments_enrollment', 'enrollment_id', unique=True),
        Index('ix_payments_transaction', 'transaction_id'),
        Index('ix_payments_gateway_transaction', 'gateway_transaction_id'),
        Index('ix_payments_student_status', 'student_id', 'status'),
        Index('ix_payments_created_at_status', 'created_at', 'status'),
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
    
    rejected_by_user = relationship(
        "User",
        foreign_keys=[rejected_by],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Payment {self.id}: {self.amount} - {self.status}>"
    
    def __str__(self) -> str:
        return f"Payment #{self.id} - {self.student.full_name} - {self.amount} PKR"
    
    # ============================================================
    # PROPERTIES
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
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if payment is cancelled."""
        return self.status == PaymentStatus.CANCELLED
    
    @property
    def has_screenshot(self) -> bool:
        """Check if screenshot is uploaded."""
        return self.screenshot_url is not None
    
    @property
    def is_refundable(self) -> bool:
        """Check if payment can be refunded."""
        return self.is_verified and not self.is_refunded
    
    @property
    def is_manual_payment(self) -> bool:
        """Check if payment is manual (screenshot-based)."""
        return self.gateway == PaymentGateway.NONE.value
    
    @property
    def is_online_payment(self) -> bool:
        """Check if payment is online (API-based)."""
        return self.gateway != PaymentGateway.NONE.value
    
    @property
    def can_retry(self) -> bool:
        """Check if payment can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "pending": "Pending",
            "awaiting_verification": "Awaiting Verification",
            "verified": "Verified",
            "rejected": "Rejected",
            "refunded": "Refunded",
            "failed": "Failed",
            "cancelled": "Cancelled",
        }
        return status_map.get(self.status.value if self.status else None, "Unknown")
    
    @property
    def display_method(self) -> str:
        """Get human-readable payment method."""
        method_map = {
            "easypaisa": "EasyPaisa",
            "jazzcash": "JazzCash",
            "bank_transfer": "Bank Transfer",
            "stripe": "Credit/Debit Card",
            "card": "Credit/Debit Card",
            "crypto": "Cryptocurrency",
        }
        return method_map.get(self.method.value if self.method else None, "Unknown")
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def upload_screenshot(self, url: str, file_size: int = None, mime_type: str = None) -> None:
        """
        Upload payment screenshot.
        
        Args:
            url: URL of the uploaded screenshot
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
        """
        self.screenshot_url = url
        self.screenshot_uploaded_at = func.now()
        self.screenshot_file_size = file_size
        self.screenshot_mime_type = mime_type
        self.status = PaymentStatus.AWAITING_VERIFICATION
    
    def verify(self, verified_by: int, notes: str = None, method: str = "manual") -> None:
        """
        Verify payment.
        
        Args:
            verified_by: Admin ID who verified the payment
            notes: Additional notes about verification
            method: Verification method (manual, api, webhook)
        """
        self.status = PaymentStatus.VERIFIED
        self.verified_by = verified_by
        self.verified_at = func.now()
        self.verification_method = method
        
        if notes:
            self.verification_notes = notes
        
        # Activate enrollment
        if self.enrollment and self.enrollment.is_pending or self.enrollment.is_payment_verification:
            self.enrollment.activate(verified_by)
    
    def reject(self, rejected_by: int, reason: str) -> None:
        """
        Reject payment.
        
        Args:
            rejected_by: Admin ID who rejected the payment
            reason: Reason for rejection
        """
        self.status = PaymentStatus.REJECTED
        self.rejected_by = rejected_by
        self.rejected_at = func.now()
        self.rejection_reason = reason
    
    def refund(self, processed_by: int, reason: str = None, refund_amount: float = None) -> None:
        """
        Refund payment.
        
        Args:
            processed_by: Admin ID who processed the refund
            reason: Reason for refund
            refund_amount: Amount to refund (if partial)
        """
        self.status = PaymentStatus.REFUNDED
        self.refund_processed_by = processed_by
        self.refunded_at = func.now()
        self.refund_reason = reason
        self.refund_amount = refund_amount if refund_amount is not None else self.amount
    
    def mark_failed(self, reason: str = None) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED
        self.rejection_reason = reason
        self.retry_count += 1
        self.last_retry_at = func.now()
    
    def mark_cancelled(self, reason: str = None) -> None:
        """Mark payment as cancelled."""
        self.status = PaymentStatus.CANCELLED
        self.rejection_reason = reason
    
    def add_transaction(self, transaction_id: str) -> None:
        """Add transaction ID from payment gateway."""
        self.transaction_id = transaction_id
    
    def add_gateway_transaction(self, gateway: str, gateway_transaction_id: str, response: dict = None) -> None:
        """
        Add gateway transaction details.
        
        Args:
            gateway: Gateway name
            gateway_transaction_id: Gateway transaction ID
            response: Raw gateway response
        """
        self.gateway = gateway
        self.gateway_transaction_id = gateway_transaction_id
        if response:
            self.gateway_response = response
    
    def add_sender(self, name: str, phone: str) -> None:
        """Add sender details."""
        self.sender_name = name
        self.sender_phone = phone
    
    def set_subscription(self, subscription_id: str, interval: str) -> None:
        """
        Set payment as recurring subscription.
        
        Args:
            subscription_id: Subscription ID from gateway
            interval: Interval (monthly, yearly)
        """
        self.is_recurring = True
        self.subscription_id = subscription_id
        self.recurring_interval = interval
    
    def cancel_subscription(self) -> None:
        """Cancel recurring subscription."""
        self.is_recurring = False
        self.subscription_cancelled_at = func.now()
    
    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.last_retry_at = func.now()
    
    def reset_retries(self) -> None:
        """Reset retry count."""
        self.retry_count = 0
        self.last_retry_at = None
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete(self) -> None:
        """Soft delete the payment."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted payment."""
        self.deleted_at = None
    
    def set_device_info(self, ip_address: str, user_agent: str, device_id: str = None, session_id: str = None) -> None:
        """Set device information."""
        self.ip_address = ip_address
        self.user_agent = user_agent
        if device_id:
            self.device_id = device_id
        if session_id:
            self.session_id = session_id
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_amount(amount: float) -> bool:
        """Validate payment amount."""
        return 0 <= amount <= 999999
    
    @staticmethod
    def validate_transaction_id(transaction_id: str) -> bool:
        """Validate transaction ID format."""
        return bool(re.match(r'^[a-zA-Z0-9\-_]+$', transaction_id)) if transaction_id else True
    
    @staticmethod
    def validate_sender_phone(phone: str) -> bool:
        """Validate sender phone number."""
        return bool(re.match(r'^[0-9+\-\(\) ]+$', phone)) if phone else True
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert payment to dictionary."""
        data = {
            "id": self.id,
            "enrollment_id": self.enrollment_id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "amount": float(self.amount),
            "method": self.method.value if self.method else None,
            "display_method": self.display_method,
            "status": self.status.value if self.status else None,
            "display_status": self.display_status,
            "payment_type": self.payment_type,
            "gateway": self.gateway,
            "is_manual": self.is_manual_payment,
            "is_online": self.is_online_payment,
            "has_screenshot": self.has_screenshot,
            "is_refundable": self.is_refundable,
            "can_retry": self.can_retry,
            "retry_count": self.retry_count,
            "sender_name": self.sender_name,
            "sender_phone": self.sender_phone,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
        }
        
        if include_sensitive:
            data.update({
                "screenshot_url": self.screenshot_url,
                "screenshot_file_size": self.screenshot_file_size,
                "screenshot_mime_type": self.screenshot_mime_type,
                "screenshot_uploaded_at": self.screenshot_uploaded_at.isoformat() if self.screenshot_uploaded_at else None,
                "easypaisa_account": self.easypaisa_account,
                "easypaisa_holder": self.easypaisa_holder,
                "verification_notes": self.verification_notes,
                "verification_method": self.verification_method,
                "rejection_reason": self.rejection_reason,
                "rejected_by": self.rejected_by,
                "refund_amount": float(self.refund_amount) if self.refund_amount else None,
                "refund_reason": self.refund_reason,
                "refund_processed_by": self.refund_processed_by,
                "refund_transaction_id": self.refund_transaction_id,
                "gateway_transaction_id": self.gateway_transaction_id,
                "gateway_response": self.gateway_response,
                "payment_intent_id": self.payment_intent_id,
                "subscription_id": self.subscription_id,
                "is_recurring": self.is_recurring,
                "recurring_interval": self.recurring_interval,
                "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
                "ip_address": str(self.ip_address) if self.ip_address else None,
                "device_id": self.device_id,
                "session_id": self.session_id,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing payment data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("screenshot_url", None)
        data.pop("easypaisa_account", None)
        data.pop("easypaisa_holder", None)
        data.pop("verification_notes", None)
        data.pop("rejection_reason", None)
        data.pop("refund_reason", None)
        data.pop("gateway_response", None)
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing payment data."""
        data = self.to_public_json()
        data.update({
            "can_view": True,
            "status_description": self.display_status,
        })
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing payment data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: PAYMENT WEBHOOK LOG (For API integrations)
# ============================================================

class PaymentWebhookLog(Base):
    """Track payment webhooks from gateways."""
    __tablename__ = "payment_webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Webhook data
    gateway = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    raw_payload = Column(JSON, nullable=False)
    
    # Processing result
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Related payment
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    
    # Security
    signature_valid = Column(Boolean, default=False, nullable=False)
    signature_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    payment = relationship("Payment", foreign_keys=[payment_id])
    
    def __repr__(self) -> str:
        return f"<PaymentWebhookLog {self.id}: {self.gateway} - {self.event_type}>"