# ============================================================
# AETHER LINK - ENROLLMENT SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# ENROLLMENT ENUMS (UPGRADED)
# ============================================================

class EnrollmentStatusEnum(str, Enum):
    """Enrollment status enumeration for schemas."""
    PENDING = "pending"
    PAYMENT_VERIFICATION = "payment_verification"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration for schemas."""
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"
    CARD = "card"        # NEW
    CRYPTO = "crypto"    # NEW


class EnrollmentSourceEnum(str, Enum):  # NEW
    """Enrollment source enumeration."""
    DIRECT = "direct"
    LEARNING_PATH = "learning_path"
    COUPON = "coupon"
    ADMIN = "admin"
    UPGRADE = "upgrade"


# ============================================================
# BASE SCHEMA
# ============================================================

class EnrollmentBase(BaseModel):
    """Base enrollment schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# ENROLLMENT CREATE SCHEMA
# ============================================================

class EnrollmentCreate(EnrollmentBase):
    """Schema for creating an enrollment."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.EASYPAISA, description="Payment method")
    payment_screenshot: Optional[str] = Field(default=None, max_length=500, description="Payment screenshot URL")
    
    # NEW: Source tracking
    source: Optional[EnrollmentSourceEnum] = Field(
        default=EnrollmentSourceEnum.DIRECT,
        description="Enrollment source"
    )
    
    # NEW: Coupon code
    coupon_code: Optional[str] = Field(default=None, max_length=50, description="Coupon code to apply")
    
    @field_validator('payment_screenshot')
    @classmethod
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

class EnrollmentUpdate(EnrollmentBase):
    """Schema for updating enrollment."""
    
    status: Optional[EnrollmentStatusEnum] = Field(default=None, description="Enrollment status")
    payment_verified: Optional[bool] = Field(default=None, description="Payment verified?")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Admin notes")
    
    # NEW: Payment rejection
    reject_payment: Optional[bool] = Field(default=None, description="Reject payment")
    rejection_reason: Optional[str] = Field(default=None, max_length=500, description="Rejection reason")
    
    # NEW: Extend expiry
    extend_expiry_days: Optional[int] = Field(default=None, ge=1, description="Extend expiry by days")


# ============================================================
# PAYMENT VERIFICATION SCHEMA (Admin)
# ============================================================

class PaymentVerification(EnrollmentBase):
    """Schema for admin verifying payment."""
    
    verified: bool = Field(..., description="Is payment verified?")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Verification notes")
    
    # NEW: Transaction ID
    transaction_id: Optional[str] = Field(default=None, max_length=100, description="Transaction ID")


# ============================================================
# PROGRESS UPDATE SCHEMA
# ============================================================

class ProgressUpdate(EnrollmentBase):
    """Schema for updating student progress."""
    
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    
    # NEW: Detailed progress
    completed_sessions: Optional[int] = Field(default=None, ge=0, description="Completed sessions")
    total_sessions: Optional[int] = Field(default=None, ge=0, description="Total sessions")
    time_spent_minutes: Optional[int] = Field(default=None, ge=0, description="Time spent in minutes")


# ============================================================
# ENROLLMENT RESPONSE SCHEMA
# ============================================================

class EnrollmentResponse(EnrollmentBase):
    """Schema for enrollment response."""
    
    id: int = Field(..., description="Enrollment ID")
    student_id: int = Field(..., description="Student ID")
    course_id: int = Field(..., description="Course ID")
    status: EnrollmentStatusEnum = Field(..., description="Enrollment status")
    
    payment_amount: float = Field(..., description="Payment amount")
    payment_method: PaymentMethodEnum = Field(..., description="Payment method")
    payment_screenshot: Optional[str] = Field(default=None, description="Payment screenshot URL")
    payment_verified: bool = Field(..., description="Payment verified?")
    payment_verified_by: Optional[int] = Field(default=None, description="Verified by (admin ID)")
    payment_verified_at: Optional[datetime] = Field(default=None, description="Verification timestamp")
    
    # NEW: Payment rejection tracking
    payment_rejected_at: Optional[datetime] = Field(default=None, description="Payment rejection timestamp")
    payment_rejection_reason: Optional[str] = Field(default=None, description="Rejection reason")
    
    # NEW: Source
    source: str = Field(default="direct", description="Enrollment source")
    source_reference_id: Optional[int] = Field(default=None, description="Source reference ID")
    source_reference_type: Optional[str] = Field(default=None, description="Source reference type")
    
    # NEW: Discount
    discount_applied: float = Field(default=0.0, description="Discount applied")
    coupon_code: Optional[str] = Field(default=None, description="Coupon code used")
    effective_paid_amount: float = Field(..., description="Effective paid amount after discount")
    
    # NEW: Progress details
    completed_sessions: int = Field(default=0, description="Completed sessions")
    total_sessions: int = Field(default=0, description="Total sessions")
    completed_materials: int = Field(default=0, description="Completed materials")
    total_materials: int = Field(default=0, description="Total materials")
    total_time_spent_minutes: int = Field(default=0, description="Total time spent in minutes")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last access time")
    engagement_score: float = Field(default=0.0, description="Engagement score")
    
    enrolled_at: datetime = Field(..., description="Enrollment date")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry date")
    completed_at: Optional[datetime] = Field(default=None, description="Completion date")
    
    progress_percentage: int = Field(default=0, description="Progress percentage (0-100)")
    notes: Optional[str] = Field(default=None, description="Admin notes")
    
    # NEW: Certificate tracking
    certificate_issued: bool = Field(default=False, description="Certificate issued")
    certificate_issued_at: Optional[datetime] = Field(default=None, description="Certificate issue date")
    certificate_id: Optional[int] = Field(default=None, description="Certificate ID")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# ENROLLMENT DETAIL RESPONSE
# ============================================================

class EnrollmentDetailResponse(EnrollmentResponse):
    """Schema for enrollment detail response with student/course info."""
    
    student_name: str = Field(..., description="Student's full name")
    student_email: str = Field(..., description="Student's email")
    student_avatar: Optional[str] = Field(default=None, description="Student's avatar")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    course_thumbnail: Optional[str] = Field(default=None, description="Course thumbnail")
    teacher_name: str = Field(..., description="Primary teacher's full name")
    
    # NEW: Course stats
    total_students_in_course: int = Field(default=0, description="Total students in course")
    
    # NEW: Payment history
    payment_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Payment history"
    )


# ============================================================
# STUDENT ENROLLMENT RESPONSE (Dashboard)
# ============================================================

class StudentEnrollmentResponse(EnrollmentBase):
    """Schema for student enrollment dashboard view."""
    
    id: int = Field(..., description="Enrollment ID")
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    course_thumbnail: Optional[str] = Field(default=None, description="Course thumbnail")
    teacher_name: str = Field(..., description="Teacher's full name")
    
    status: EnrollmentStatusEnum = Field(..., description="Enrollment status")
    progress_percentage: int = Field(default=0, description="Progress percentage")
    
    enrolled_at: datetime = Field(..., description="Enrollment date")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry date")
    
    # NEW: Days until expiry
    days_until_expiry: int = Field(default=-1, description="Days until expiry")
    is_expiring_soon: bool = Field(default=False, description="Expiring soon (within 7 days)")
    
    total_sessions: int = Field(default=0, description="Total sessions")
    completed_sessions: int = Field(default=0, description="Completed sessions")
    missed_sessions: int = Field(default=0, description="Missed sessions")
    
    # NEW: Certificate
    has_certificate: bool = Field(default=False, description="Has certificate")
    certificate_url: Optional[str] = Field(default=None, description="Certificate URL")
    
    next_session_date: Optional[datetime] = Field(default=None, description="Next session date")
    next_session_title: Optional[str] = Field(default=None, description="Next session title")
    
    # NEW: Recent activity
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last access time")
    total_time_spent_minutes: int = Field(default=0, description="Total time spent in minutes")


# ============================================================
# ENROLLMENT LIST REQUEST (Filters)
# ============================================================

class EnrollmentListRequest(EnrollmentBase):
    """Schema for enrollment list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by student or course")
    status: Optional[EnrollmentStatusEnum] = Field(default=None, description="Filter by status")
    source: Optional[EnrollmentSourceEnum] = Field(default=None, description="Filter by source")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    student_id: Optional[int] = Field(default=None, description="Filter by student")
    payment_verified: Optional[bool] = Field(default=None, description="Filter by payment verification")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# ENROLLMENT LIST RESPONSE
# ============================================================

class EnrollmentListResponse(EnrollmentBase):
    """Schema for paginated enrollment list response."""
    
    enrollments: List[EnrollmentResponse] = Field(..., description="List of enrollments")
    total: int = Field(..., description="Total number of enrollments")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# ENROLLMENT STATISTICS (Admin View)
# ============================================================

class EnrollmentStatistics(EnrollmentBase):
    """Schema for enrollment statistics."""
    
    total_enrollments: int = Field(..., description="Total enrollments")
    pending: int = Field(..., description="Pending enrollments")
    payment_verification: int = Field(..., description="In payment verification")
    active: int = Field(..., description="Active enrollments")
    completed: int = Field(..., description="Completed enrollments")
    cancelled: int = Field(..., description="Cancelled enrollments")
    expired: int = Field(..., description="Expired enrollments")
    
    # NEW: Revenue stats
    total_revenue: float = Field(default=0.0, description="Total revenue")
    average_price: float = Field(default=0.0, description="Average enrollment price")
    total_discount_applied: float = Field(default=0.0, description="Total discount applied")
    
    # NEW: Source breakdown
    source_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Enrollments by source"
    )
    
    # NEW: Course breakdown
    popular_courses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most popular courses"
    )
    
    # NEW: Trends
    daily_enrollments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily enrollment trends"
    )
    
    # NEW: Completion stats
    completion_rate: float = Field(default=0.0, description="Overall completion rate")
    average_completion_days: float = Field(default=0.0, description="Average days to complete")


# ============================================================
# ENROLLMENT BULK ACTION
# ============================================================

class EnrollmentBulkAction(EnrollmentBase):
    """Schema for bulk enrollment actions."""
    
    enrollment_ids: List[int] = Field(..., description="List of enrollment IDs")
    action: str = Field(..., description="Action to perform (verify, cancel, complete, delete)")
    notes: Optional[str] = Field(default=None, description="Action notes")


# ============================================================
# ENROLLMENT EXPORT REQUEST
# ============================================================

class EnrollmentExportRequest(EnrollmentBase):
    """Schema for enrollment export request."""
    
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    status: Optional[EnrollmentStatusEnum] = Field(default=None, description="Filter by status")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    format: str = Field(default="csv", description="Export format (csv, excel, pdf)")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "EnrollmentStatusEnum",
    "PaymentMethodEnum",
    "EnrollmentSourceEnum",
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "PaymentVerification",
    "ProgressUpdate",
    "EnrollmentResponse",
    "EnrollmentDetailResponse",
    "StudentEnrollmentResponse",
    "EnrollmentListRequest",
    "EnrollmentListResponse",
    "EnrollmentStatistics",
    "EnrollmentBulkAction",
    "EnrollmentExportRequest",
]