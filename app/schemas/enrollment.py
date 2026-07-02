# ============================================================
# AETHER LINK - ENROLLMENT SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# ENROLLMENT STATUS ENUM
# ============================================================

class EnrollmentStatusEnum(str, Enum):
    """Enrollment status enumeration for schemas."""
    PENDING = "pending"
    PAYMENT_VERIFICATION = "payment_verification"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


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
# ENROLLMENT CREATE SCHEMA
# ============================================================

class EnrollmentCreate(BaseModel):
    """Schema for creating an enrollment."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.EASYPAISA, description="Payment method")
    payment_screenshot: Optional[str] = Field(None, max_length=500, description="Payment screenshot URL")
    
    @validator('payment_screenshot')
    def validate_screenshot(cls, v: Optional[str]) -> Optional[str]:
        """Validate screenshot URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Screenshot must be a valid URL')
        return v


# ============================================================
# ENROLLMENT UPDATE SCHEMA
# ============================================================

class EnrollmentUpdate(BaseModel):
    """Schema for updating enrollment status."""
    
    status: Optional[EnrollmentStatusEnum] = Field(None, description="Enrollment status")
    payment_verified: Optional[bool] = Field(None, description="Payment verified?")
    notes: Optional[str] = Field(None, max_length=1000, description="Admin notes")


# ============================================================
# PAYMENT VERIFICATION SCHEMA (Admin)
# ============================================================

class PaymentVerification(BaseModel):
    """Schema for admin verifying payment."""
    
    verified: bool = Field(..., description="Is payment verified?")
    notes: Optional[str] = Field(None, max_length=1000, description="Verification notes")


# ============================================================
# PROGRESS UPDATE SCHEMA
# ============================================================

class ProgressUpdate(BaseModel):
    """Schema for updating student progress."""
    
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")


# ============================================================
# ENROLLMENT RESPONSE SCHEMA
# ============================================================

class EnrollmentResponse(BaseModel):
    """Schema for enrollment response."""
    
    id: int = Field(..., description="Enrollment ID")
    student_id: int = Field(..., description="Student ID")
    course_id: int = Field(..., description="Course ID")
    status: EnrollmentStatusEnum = Field(..., description="Enrollment status")
    
    payment_amount: float = Field(..., description="Payment amount")
    payment_method: PaymentMethodEnum = Field(..., description="Payment method")
    payment_screenshot: Optional[str] = Field(None, description="Payment screenshot URL")
    payment_verified: bool = Field(..., description="Payment verified?")
    payment_verified_by: Optional[int] = Field(None, description="Verified by (admin ID)")
    payment_verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    
    enrolled_at: datetime = Field(..., description="Enrollment date")
    expires_at: Optional[datetime] = Field(None, description="Expiry date")
    completed_at: Optional[datetime] = Field(None, description="Completion date")
    
    progress_percentage: int = Field(0, description="Progress percentage (0-100)")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


# ============================================================
# ENROLLMENT DETAIL RESPONSE
# ============================================================

class EnrollmentDetailResponse(EnrollmentResponse):
    """Schema for enrollment detail response with student/course info."""
    
    student_name: str = Field(..., description="Student's full name")
    student_email: str = Field(..., description="Student's email")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    teacher_name: str = Field(..., description="Teacher's full name")


# ============================================================
# STUDENT ENROLLMENT RESPONSE
# ============================================================

class StudentEnrollmentResponse(BaseModel):
    """Schema for student enrollment dashboard view."""
    
    id: int = Field(..., description="Enrollment ID")
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    course_thumbnail: Optional[str] = Field(None, description="Course thumbnail")
    teacher_name: str = Field(..., description="Teacher's full name")
    
    status: EnrollmentStatusEnum = Field(..., description="Enrollment status")
    progress_percentage: int = Field(0, description="Progress percentage")
    
    enrolled_at: datetime = Field(..., description="Enrollment date")
    expires_at: Optional[datetime] = Field(None, description="Expiry date")
    
    total_sessions: int = Field(0, description="Total sessions")
    completed_sessions: int = Field(0, description="Completed sessions")
    missed_sessions: int = Field(0, description="Missed sessions")
    
    next_session_date: Optional[datetime] = Field(None, description="Next session date")
    next_session_title: Optional[str] = Field(None, description="Next session title")


# ============================================================
# ENROLLMENT LIST RESPONSE
# ============================================================

class EnrollmentListResponse(BaseModel):
    """Schema for paginated enrollment list response."""
    
    enrollments: List[EnrollmentResponse] = Field(..., description="List of enrollments")
    total: int = Field(..., description="Total number of enrollments")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "EnrollmentStatusEnum",
    "PaymentMethodEnum",
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "PaymentVerification",
    "ProgressUpdate",
    "EnrollmentResponse",
    "EnrollmentDetailResponse",
    "StudentEnrollmentResponse",
    "EnrollmentListResponse",
]