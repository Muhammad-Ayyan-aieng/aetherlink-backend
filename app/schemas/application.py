# ============================================================
# AETHER LINK - APPLICATION SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# APPLICATION STATUS ENUM
# ============================================================

class ApplicationStatusEnum(str, Enum):
    """Application status enumeration for schemas."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================
# SUBMIT APPLICATION SCHEMA
# ============================================================

class ApplicationSubmit(BaseModel):
    """Schema for submitting an application."""

    email: EmailStr = Field(..., description="Student email")
    full_name: str = Field(..., min_length=2, max_length=100, description="Student full name")
    phone: Optional[str] = Field(None, max_length=20, description="Student phone number")
    course_id: int = Field(..., gt=0, description="Course ID")
    message: Optional[str] = Field(None, max_length=500, description="Additional message")

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


# ============================================================
# APPLICATION UPDATE STATUS SCHEMA
# ============================================================

class ApplicationUpdateStatus(BaseModel):
    """Schema for updating application status (admin)."""

    notes: Optional[str] = Field(None, max_length=500, description="Admin notes")

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

class ApplicationResponse(BaseModel):
    """Schema for application response."""

    id: int = Field(..., description="Application ID")
    email: str = Field(..., description="Student email")
    full_name: str = Field(..., description="Student full name")
    phone: Optional[str] = Field(None, description="Student phone number")
    course_id: int = Field(..., description="Course ID")
    course_title: Optional[str] = Field(None, description="Course title")
    message: Optional[str] = Field(None, description="Additional message")
    status: ApplicationStatusEnum = Field(..., description="Application status")
    admin_notes: Optional[str] = Field(None, description="Admin notes")
    approved_by: Optional[int] = Field(None, description="Admin who approved/rejected")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = {"from_attributes": True}


# ============================================================
# APPLICATION LIST RESPONSE
# ============================================================

class ApplicationListResponse(BaseModel):
    """Schema for paginated application list response."""

    applications: List[ApplicationResponse] = Field(..., description="List of applications")
    total: int = Field(..., description="Total number of applications")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# APPLICATION STATISTICS
# ============================================================

class ApplicationStats(BaseModel):
    """Schema for application statistics."""

    total: int = Field(..., description="Total applications")
    pending: int = Field(..., description="Pending applications")
    approved: int = Field(..., description="Approved applications")
    rejected: int = Field(..., description="Rejected applications")
    recent_applications: List[ApplicationResponse] = Field(default_factory=list, description="Recent applications")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ApplicationStatusEnum",
    "ApplicationSubmit",
    "ApplicationUpdateStatus",
    "ApplicationResponse",
    "ApplicationListResponse",
    "ApplicationStats",
]