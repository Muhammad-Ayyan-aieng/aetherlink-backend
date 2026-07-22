# ============================================================
# AETHER LINK - APPLICATION SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# APPLICATION STATUS ENUM (UPGRADED)
# ============================================================

class ApplicationStatusEnum(str, Enum):
    """Application status enumeration for schemas."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"   # NEW
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"         # NEW


class ApplicationSourceEnum(str, Enum):  # NEW
    """Application source enumeration."""
    WEBSITE = "website"
    LANDING_PAGE = "landing_page"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


class ApplicationPriorityEnum(str, Enum):  # NEW
    """Application priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================
# BASE SCHEMA
# ============================================================

class ApplicationBase(BaseModel):
    """Base application schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# SUBMIT APPLICATION SCHEMA
# ============================================================

class ApplicationSubmit(ApplicationBase):
    """Schema for submitting an application."""

    email: EmailStr = Field(..., description="Student email")
    full_name: str = Field(..., min_length=2, max_length=100, description="Student full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Student phone number")
    course_id: int = Field(..., gt=0, description="Course ID")
    message: Optional[str] = Field(default=None, max_length=5000, description="Additional message")
    
    # NEW: Source tracking
    source: Optional[ApplicationSourceEnum] = Field(
        default=ApplicationSourceEnum.WEBSITE,
        description="Application source"
    )
    referral_source: Optional[str] = Field(default=None, max_length=255, description="How they heard about us")
    
    # NEW: Additional applicant info
    education: Optional[str] = Field(default=None, max_length=255, description="Highest education")
    institution: Optional[str] = Field(default=None, max_length=255, description="Institution name")
    experience_years: Optional[int] = Field(default=None, ge=0, description="Years of experience")
    current_occupation: Optional[str] = Field(default=None, max_length=255, description="Current occupation")
    expected_start_date: Optional[datetime] = Field(default=None, description="Expected start date")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower().strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None or v == "":
            return v
        import re
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v: Optional[str]) -> Optional[str]:
        """Validate source."""
        if v is None:
            return ApplicationSourceEnum.WEBSITE.value
        return v


# ============================================================
# APPLICATION UPDATE SCHEMA (Admin)
# ============================================================

class ApplicationUpdateStatus(ApplicationBase):
    """Schema for updating application status (admin)."""

    status: ApplicationStatusEnum = Field(..., description="New application status")
    notes: Optional[str] = Field(default=None, max_length=500, description="Admin notes")
    
    # NEW: Priority update
    priority: Optional[ApplicationPriorityEnum] = Field(default=None, description="Application priority")
    
    # NEW: Follow-up scheduling
    follow_up_date: Optional[datetime] = Field(default=None, description="Next follow-up date")
    follow_up_notes: Optional[str] = Field(default=None, max_length=500, description="Follow-up notes")

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """Validate notes."""
        if v is not None and len(v.strip()) < 1:
            return None
        return v


# ============================================================
# APPLICATION RESPONSE SCHEMA
# ============================================================

class ApplicationResponse(ApplicationBase):
    """Schema for application response."""

    id: int = Field(..., description="Application ID")
    email: str = Field(..., description="Student email")
    full_name: str = Field(..., description="Student full name")
    phone: Optional[str] = Field(default=None, description="Student phone number")
    course_id: int = Field(..., description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    message: Optional[str] = Field(default=None, description="Additional message")
    status: ApplicationStatusEnum = Field(..., description="Application status")
    
    # NEW: Priority
    priority: str = Field(default="normal", description="Application priority")
    
    # NEW: Source
    source: str = Field(default="website", description="Application source")
    referral_source: Optional[str] = Field(default=None, description="How they heard about us")
    
    # NEW: Applicant details
    education: Optional[str] = Field(default=None, description="Highest education")
    institution: Optional[str] = Field(default=None, description="Institution name")
    experience_years: Optional[int] = Field(default=None, description="Years of experience")
    current_occupation: Optional[str] = Field(default=None, description="Current occupation")
    expected_start_date: Optional[datetime] = Field(default=None, description="Expected start date")
    
    admin_notes: Optional[str] = Field(default=None, description="Admin notes")
    approved_by: Optional[int] = Field(default=None, description="Admin who approved/rejected")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    rejected_at: Optional[datetime] = Field(default=None, description="Rejection timestamp")
    rejected_by: Optional[int] = Field(default=None, description="Admin who rejected")
    
    # NEW: Withdrawal info
    withdrawn_at: Optional[datetime] = Field(default=None, description="Withdrawal timestamp")
    withdrawal_reason: Optional[str] = Field(default=None, description="Withdrawal reason")
    
    # NEW: Follow-up info
    follow_up_count: int = Field(default=0, description="Number of follow-ups")
    last_follow_up_at: Optional[datetime] = Field(default=None, description="Last follow-up timestamp")
    next_follow_up_at: Optional[datetime] = Field(default=None, description="Next follow-up date")
    
    # NEW: Conversion info
    converted_to_enrollment_id: Optional[int] = Field(default=None, description="Converted enrollment ID")
    converted_at: Optional[datetime] = Field(default=None, description="Conversion timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# APPLICATION LIST REQUEST (Filters)
# ============================================================

class ApplicationListRequest(ApplicationBase):
    """Schema for application list request with filters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by name or email")
    status: Optional[ApplicationStatusEnum] = Field(default=None, description="Filter by status")
    priority: Optional[ApplicationPriorityEnum] = Field(default=None, description="Filter by priority")
    source: Optional[ApplicationSourceEnum] = Field(default=None, description="Filter by source")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# APPLICATION LIST RESPONSE
# ============================================================

class ApplicationListResponse(ApplicationBase):
    """Schema for paginated application list response."""

    applications: List[ApplicationResponse] = Field(..., description="List of applications")
    total: int = Field(..., description="Total number of applications")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# APPLICATION STATISTICS
# ============================================================

class ApplicationStats(ApplicationBase):
    """Schema for application statistics."""

    total: int = Field(..., description="Total applications")
    pending: int = Field(..., description="Pending applications")
    under_review: int = Field(default=0, description="Under review applications")  # NEW
    approved: int = Field(..., description="Approved applications")
    rejected: int = Field(..., description="Rejected applications")
    withdrawn: int = Field(default=0, description="Withdrawn applications")  # NEW
    
    # NEW: Priority breakdown
    low_priority: int = Field(default=0, description="Low priority applications")
    normal_priority: int = Field(default=0, description="Normal priority applications")
    high_priority: int = Field(default=0, description="High priority applications")
    urgent_priority: int = Field(default=0, description="Urgent priority applications")
    
    # NEW: Source breakdown
    source_breakdown: Dict[str, int] = Field(default_factory=dict, description="Applications by source")
    
    # NEW: Conversion stats
    conversion_rate: float = Field(default=0.0, description="Conversion rate (approved → enrolled)")
    
    # NEW: Time metrics
    average_response_days: float = Field(default=0.0, description="Average response time in days")
    
    # NEW: Recent applications
    recent_applications: List[ApplicationResponse] = Field(
        default_factory=list,
        description="Recent applications"
    )


# ============================================================
# APPLICATION FOLLOW-UP SCHEMA
# ============================================================

class ApplicationFollowUp(ApplicationBase):
    """Schema for application follow-up."""

    application_id: int = Field(..., description="Application ID")
    notes: str = Field(..., min_length=1, max_length=500, description="Follow-up notes")
    scheduled_date: Optional[datetime] = Field(default=None, description="Next scheduled follow-up")


class ApplicationBulkAction(ApplicationBase):
    """Schema for bulk application actions."""

    application_ids: List[int] = Field(..., description="List of application IDs")
    action: str = Field(..., description="Action to perform (approve, reject, delete)")
    notes: Optional[str] = Field(default=None, description="Action notes")


# ============================================================
# APPLICATION CONVERT SCHEMA
# ============================================================

class ApplicationConvertRequest(ApplicationBase):
    """Schema for converting application to enrollment."""

    application_id: int = Field(..., description="Application ID")
    create_user: bool = Field(default=True, description="Create user account if doesn't exist")
    enrollment_notes: Optional[str] = Field(default=None, description="Enrollment notes")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ApplicationStatusEnum",
    "ApplicationSourceEnum",
    "ApplicationPriorityEnum",
    "ApplicationSubmit",
    "ApplicationUpdateStatus",
    "ApplicationResponse",
    "ApplicationListRequest",
    "ApplicationListResponse",
    "ApplicationStats",
    "ApplicationFollowUp",
    "ApplicationBulkAction",
    "ApplicationConvertRequest",
]