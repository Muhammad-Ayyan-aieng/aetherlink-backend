# ============================================================
# AETHER LINK - PAYMENT SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# PAYMENT ENUMS (UPGRADED)
# ============================================================

class PaymentStatusEnum(str, Enum):
    """Payment status enumeration for schemas."""
    PENDING = "pending"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    FAILED = "failed"        # NEW
    CANCELLED = "cancelled"  # NEW


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration for schemas."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"
    CARD = "card"            # NEW
    CRYPTO = "crypto"        # NEW


class PaymentTypeEnum(str, Enum):  # NEW
    """Payment type enumeration."""
    COURSE_FEE = "course_fee"
    SUBSCRIPTION = "subscription"
    INVOICE = "invoice"
    REFUND = "refund"


class PaymentGatewayEnum(str, Enum):  # NEW
    """Payment gateway enumeration."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    PAYPAL = "paypal"
    NONE = "none"  # Manual payment


# ============================================================
# BASE SCHEMA
# ============================================================

class PaymentBase(BaseModel):
    """Base payment schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# PAYMENT INITIATE SCHEMA
# ============================================================

class PaymentInitiate(PaymentBase):
    """Schema for initiating a payment."""
    
    enrollment_id: int = Field(..., gt=0, description="Enrollment ID")
    method: PaymentMethodEnum = Field(default=PaymentMethodEnum.EASYPAISA, description="Payment method")
    
    # NEW: Payment type
    payment_type: Optional[PaymentTypeEnum] = Field(
        default=PaymentTypeEnum.COURSE_FEE,
        description="Payment type"
    )
    
    # NEW: Gateway (for online payments)
    gateway: Optional[PaymentGatewayEnum] = Field(
        default=PaymentGatewayEnum.NONE,
        description="Payment gateway"
    )
    
    @field_validator('enrollment_id')
    @classmethod
    def validate_enrollment(cls, v: int) -> int:
        """Validate enrollment ID."""
        if v <= 0:
            raise ValueError('Invalid enrollment ID')
        return v


# ============================================================
# PAYMENT UPLOAD SCREENSHOT SCHEMA
# ============================================================

class PaymentUploadScreenshot(PaymentBase):
    """Schema for uploading payment screenshot."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID")
    screenshot_url: str = Field(..., max_length=500, description="Screenshot URL")
    transaction_id: Optional[str] = Field(default=None, max_length=100, description="Transaction ID")
    sender_name: Optional[str] = Field(default=None, max_length=255, description="Sender name")
    sender_phone: Optional[str] = Field(default=None, max_length=20, description="Sender phone")
    
    # NEW: Screenshot metadata
    screenshot_file_size: Optional[int] = Field(default=None, ge=0, description="Screenshot file size in bytes")
    screenshot_mime_type: Optional[str] = Field(default=None, max_length=50, description="Screenshot MIME type")
    
    @field_validator('screenshot_url')
    @classmethod
    def validate_screenshot(cls, v: str) -> str:
        """Validate screenshot URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Screenshot URL must be valid')
        return v
    
    @field_validator('transaction_id')
    @classmethod
    def validate_transaction_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate transaction ID format."""
        if v is None:
            return v
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Transaction ID must be alphanumeric')
        return v
    
    @field_validator('sender_phone')
    @classmethod
    def validate_sender_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate sender phone number."""
        if v is None:
            return v
        import re
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v


# ============================================================
# PAYMENT VERIFY SCHEMA (Admin)
# ============================================================

class PaymentVerify(PaymentBase):
    """Schema for admin verifying payment."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID")
    notes: Optional[str] = Field(default=None, max_length=500, description="Verification notes")
    
    # NEW: Verification method
    verification_method: Optional[str] = Field(
        default="manual",
        description="Verification method (manual, api, webhook)"
    )


# ============================================================
# PAYMENT REJECT SCHEMA (Admin)
# ============================================================

class PaymentReject(PaymentBase):
    """Schema for admin rejecting payment."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID")
    reason: str = Field(..., min_length=5, max_length=500, description="Rejection reason")


# ============================================================
# PAYMENT REFUND SCHEMA (Admin)
# ============================================================

class PaymentRefund(PaymentBase):
    """Schema for refunding a payment (admin)."""

    payment_id: int = Field(..., gt=0, description="Payment ID to refund")
    amount: Optional[float] = Field(default=None, ge=0, description="Amount to refund (if partial)")
    reason: Optional[str] = Field(default=None, max_length=500, description="Refund reason")
    
    # NEW: Refund note
    note: Optional[str] = Field(default=None, max_length=500, description="Internal refund note")


# ============================================================
# PAYMENT RETRY SCHEMA (NEW)
# ============================================================

class PaymentRetry(PaymentBase):
    """Schema for retrying a failed payment."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID to retry")
    method: Optional[PaymentMethodEnum] = Field(default=None, description="New payment method (optional)")


# ============================================================
# PAYMENT RESPONSE SCHEMA
# ============================================================

class PaymentResponse(PaymentBase):
    """Schema for payment record response."""
    
    id: int = Field(..., description="Payment ID")
    enrollment_id: int = Field(..., description="Enrollment ID")
    student_id: int = Field(..., description="Student ID")
    
    amount: float = Field(..., description="Payment amount")
    method: PaymentMethodEnum = Field(..., description="Payment method")
    status: PaymentStatusEnum = Field(..., description="Payment status")
    
    # NEW: Payment type and gateway
    payment_type: str = Field(default="course_fee", description="Payment type")
    gateway: str = Field(default="none", description="Payment gateway")
    gateway_transaction_id: Optional[str] = Field(default=None, description="Gateway transaction ID")
    
    easypaisa_account: Optional[str] = Field(default=None, description="Easy Paisa account")
    easypaisa_holder: Optional[str] = Field(default=None, description="Easy Paisa holder")
    sender_name: Optional[str] = Field(default=None, description="Sender name")
    sender_phone: Optional[str] = Field(default=None, description="Sender phone")
    transaction_id: Optional[str] = Field(default=None, description="Transaction ID")
    
    screenshot_url: Optional[str] = Field(default=None, description="Screenshot URL")
    screenshot_uploaded_at: Optional[datetime] = Field(default=None, description="Screenshot upload time")
    
    # NEW: Screenshot metadata
    screenshot_file_size: Optional[int] = Field(default=None, description="Screenshot file size")
    screenshot_mime_type: Optional[str] = Field(default=None, description="Screenshot MIME type")
    
    verified_by: Optional[int] = Field(default=None, description="Verified by (admin ID)")
    verified_at: Optional[datetime] = Field(default=None, description="Verification timestamp")
    verification_notes: Optional[str] = Field(default=None, description="Verification notes")
    
    # NEW: Verification method
    verification_method: Optional[str] = Field(default=None, description="Verification method")
    
    rejected_at: Optional[datetime] = Field(default=None, description="Rejection timestamp")
    rejection_reason: Optional[str] = Field(default=None, description="Rejection reason")
    
    refunded_at: Optional[datetime] = Field(default=None, description="Refund timestamp")
    refund_amount: Optional[float] = Field(default=None, description="Refund amount")
    refund_reason: Optional[str] = Field(default=None, description="Refund reason")
    refund_processed_by: Optional[int] = Field(default=None, description="Refund processed by (admin ID)")
    
    # NEW: Retry tracking
    retry_count: int = Field(default=0, description="Number of retry attempts")
    can_retry: bool = Field(default=False, description="Can retry payment")
    
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    
    # NEW: Device info
    device_id: Optional[str] = Field(default=None, description="Device ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# PAYMENT HISTORY RESPONSE (Student View)
# ============================================================

class PaymentHistoryResponse(PaymentBase):
    """Schema for student payment history."""
    
    id: int = Field(..., description="Payment ID")
    amount: float = Field(..., description="Payment amount")
    method: PaymentMethodEnum = Field(..., description="Payment method")
    status: PaymentStatusEnum = Field(..., description="Payment status")
    
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    
    transaction_id: Optional[str] = Field(default=None, description="Transaction ID")
    screenshot_url: Optional[str] = Field(default=None, description="Screenshot URL")
    
    # NEW: Display info
    display_status: str = Field(..., description="Human-readable status")
    display_method: str = Field(..., description="Human-readable method")
    
    created_at: datetime = Field(..., description="Payment date")
    verified_at: Optional[datetime] = Field(default=None, description="Verification date")


# ============================================================
# PAYMENT LIST REQUEST (Filters)
# ============================================================

class PaymentListRequest(PaymentBase):
    """Schema for payment list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by student or transaction ID")
    status: Optional[PaymentStatusEnum] = Field(default=None, description="Filter by status")
    method: Optional[PaymentMethodEnum] = Field(default=None, description="Filter by method")
    payment_type: Optional[PaymentTypeEnum] = Field(default=None, description="Filter by payment type")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    student_id: Optional[int] = Field(default=None, description="Filter by student")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# PAYMENT LIST RESPONSE (Admin)
# ============================================================

class PaymentListResponse(PaymentBase):
    """Schema for paginated payment list response."""
    
    payments: List[PaymentResponse] = Field(..., description="List of payments")
    total: int = Field(..., description="Total number of payments")
    pending_count: int = Field(..., description="Pending payments count")
    awaiting_count: int = Field(..., description="Awaiting verification count")
    verified_count: int = Field(..., description="Verified payments count")
    rejected_count: int = Field(..., description="Rejected payments count")
    refunded_count: int = Field(..., description="Refunded payments count")
    total_revenue: float = Field(..., description="Total verified revenue")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# PAYMENT SUMMARY (Admin Dashboard)
# ============================================================

class PaymentSummary(PaymentBase):
    """Schema for payment summary on admin dashboard."""
    
    total_payments: int = Field(..., description="Total payments")
    total_revenue: float = Field(..., description="Total revenue")
    pending_verification: int = Field(..., description="Pending verification count")
    verified_today: int = Field(..., description="Verified today count")
    revenue_this_month: float = Field(..., description="Revenue this month")
    revenue_last_month: float = Field(..., description="Revenue last month")
    growth_percentage: float = Field(..., description="Month over month growth")
    
    # NEW: Detailed breakdown
    status_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Payments by status"
    )
    method_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Payments by method"
    )
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Payments by type"
    )
    
    # NEW: Revenue by course
    top_courses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top revenue courses"
    )
    
    # NEW: Monthly trends
    monthly_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Monthly revenue trends"
    )


# ============================================================
# PAYMENT WEBHOOK SCHEMA (NEW)
# ============================================================

class PaymentWebhook(PaymentBase):
    """Schema for payment gateway webhook."""
    
    gateway: PaymentGatewayEnum = Field(..., description="Payment gateway")
    event: str = Field(..., description="Webhook event type")
    payload: Dict[str, Any] = Field(..., description="Raw webhook payload")
    signature: Optional[str] = Field(default=None, description="Webhook signature")
    timestamp: Optional[datetime] = Field(default=None, description="Webhook timestamp")


class PaymentWebhookResponse(PaymentBase):
    """Schema for webhook processing response."""
    
    success: bool = Field(..., description="Processing success")
    message: str = Field(..., description="Status message")
    payment_id: Optional[int] = Field(default=None, description="Processed payment ID")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PaymentStatusEnum",
    "PaymentMethodEnum",
    "PaymentTypeEnum",
    "PaymentGatewayEnum",
    "PaymentInitiate",
    "PaymentUploadScreenshot",
    "PaymentVerify",
    "PaymentReject",
    "PaymentRefund",
    "PaymentRetry",
    "PaymentResponse",
    "PaymentHistoryResponse",
    "PaymentListRequest",
    "PaymentListResponse",
    "PaymentSummary",
    "PaymentWebhook",
    "PaymentWebhookResponse",
]