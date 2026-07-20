# ============================================================
# AETHER LINK - PAYMENT SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# PAYMENT STATUS ENUM
# ============================================================

class PaymentStatusEnum(str, Enum):
    """Payment status enumeration for schemas."""
    PENDING = "pending"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"


# ============================================================
# PAYMENT METHOD ENUM
# ============================================================

class PaymentMethodEnum(str, Enum):
    """Payment method enumeration for schemas."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"


# ============================================================
# PAYMENT INITIATE SCHEMA
# ============================================================

class PaymentInitiate(BaseModel):
    """Schema for initiating a payment."""
    
    enrollment_id: int = Field(..., gt=0, description="Enrollment ID")
    method: PaymentMethodEnum = Field(default=PaymentMethodEnum.EASYPAISA, description="Payment method")
    
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

class PaymentUploadScreenshot(BaseModel):
    """Schema for uploading payment screenshot."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID")
    screenshot_url: str = Field(..., max_length=500, description="Screenshot URL")
    transaction_id: Optional[str] = Field(None, max_length=100, description="Easy Paisa transaction ID")
    sender_name: Optional[str] = Field(None, max_length=255, description="Sender name")
    sender_phone: Optional[str] = Field(None, max_length=20, description="Sender phone")
    
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
        # Basic alphanumeric validation
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Transaction ID must be alphanumeric')
        return v


# ============================================================
# PAYMENT VERIFY SCHEMA (Admin)
# ============================================================

class PaymentVerify(BaseModel):
    """Schema for admin verifying payment."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID")
    notes: Optional[str] = Field(None, max_length=500, description="Verification notes")


# ============================================================
# PAYMENT REJECT SCHEMA (Admin)
# ============================================================

class PaymentReject(BaseModel):
    """Schema for admin rejecting payment."""
    
    payment_id: int = Field(..., gt=0, description="Payment ID")
    reason: str = Field(..., min_length=5, max_length=500, description="Rejection reason")


class PaymentRefund(BaseModel):
    """Schema for refunding a payment (admin)."""

    payment_id: int = Field(..., gt=0, description="Payment ID to refund")
    reason: Optional[str] = Field(None, max_length=500, description="Optional refund reason")


# ============================================================
# PAYMENT RESPONSE SCHEMA
# ============================================================

class PaymentResponse(BaseModel):
    """Schema for payment record response."""
    
    id: int = Field(..., description="Payment ID")
    enrollment_id: int = Field(..., description="Enrollment ID")
    student_id: int = Field(..., description="Student ID")
    
    amount: float = Field(..., description="Payment amount")
    method: PaymentMethodEnum = Field(..., description="Payment method")
    status: PaymentStatusEnum = Field(..., description="Payment status")
    
    easypaisa_account: Optional[str] = Field(None, description="Easy Paisa account")
    easypaisa_holder: Optional[str] = Field(None, description="Easy Paisa holder")
    sender_name: Optional[str] = Field(None, description="Sender name")
    sender_phone: Optional[str] = Field(None, description="Sender phone")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL")
    screenshot_uploaded_at: Optional[datetime] = Field(None, description="Screenshot upload time")
    
    verified_by: Optional[int] = Field(None, description="Verified by (admin ID)")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    verification_notes: Optional[str] = Field(None, description="Verification notes")
    
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    
    refunded_at: Optional[datetime] = Field(None, description="Refund timestamp")
    refund_reason: Optional[str] = Field(None, description="Refund reason")
    refund_processed_by: Optional[int] = Field(None, description="Refund processed by (admin ID)")
    
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = {"from_attributes": True}


# ============================================================
# PAYMENT HISTORY RESPONSE (Student View)
# ============================================================

class PaymentHistoryResponse(BaseModel):
    """Schema for student payment history."""
    
    id: int = Field(..., description="Payment ID")
    amount: float = Field(..., description="Payment amount")
    method: PaymentMethodEnum = Field(..., description="Payment method")
    status: PaymentStatusEnum = Field(..., description="Payment status")
    
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL")
    
    created_at: datetime = Field(..., description="Payment date")
    verified_at: Optional[datetime] = Field(None, description="Verification date")


# ============================================================
# PAYMENT LIST RESPONSE (Admin)
# ============================================================

class PaymentListResponse(BaseModel):
    """Schema for paginated payment list response."""
    
    payments: List[PaymentResponse] = Field(..., description="List of payments")
    total: int = Field(..., description="Total number of payments")
    pending_count: int = Field(..., description="Pending payments count")
    verified_count: int = Field(..., description="Verified payments count")
    rejected_count: int = Field(..., description="Rejected payments count")
    total_revenue: float = Field(..., description="Total verified revenue")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# PAYMENT SUMMARY (Admin Dashboard)
# ============================================================

class PaymentSummary(BaseModel):
    """Schema for payment summary on admin dashboard."""
    
    total_payments: int = Field(..., description="Total payments")
    total_revenue: float = Field(..., description="Total revenue")
    pending_verification: int = Field(..., description="Pending verification count")
    verified_today: int = Field(..., description="Verified today count")
    revenue_this_month: float = Field(..., description="Revenue this month")
    revenue_last_month: float = Field(..., description="Revenue last month")
    growth_percentage: float = Field(..., description="Month over month growth")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PaymentStatusEnum",
    "PaymentMethodEnum",
    "PaymentInitiate",
    "PaymentUploadScreenshot",
    "PaymentVerify",
    "PaymentReject",
    "PaymentResponse",
    "PaymentHistoryResponse",
    "PaymentListResponse",
    "PaymentSummary",
]