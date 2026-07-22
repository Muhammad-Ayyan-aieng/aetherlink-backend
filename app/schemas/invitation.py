# ============================================================
# AETHER LINK - INVITATION SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# INVITATION ENUMS (NEW)
# ============================================================

class InvitationStatusEnum(str, Enum):
    """Invitation status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"
    RESENT = "resent"


# ============================================================
# BASE SCHEMA
# ============================================================

class InvitationBase(BaseModel):
    """Base invitation schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# INVITE TEACHER SCHEMA (Admin)
# ============================================================

class InviteTeacher(InvitationBase):
    """Schema for admin inviting a teacher."""
    
    email: EmailStr = Field(..., description="Teacher's email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="Teacher's full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Teacher's phone number")
    
    # NEW: Course assignment
    course_id: Optional[int] = Field(default=None, gt=0, description="Course ID to assign teacher to")
    
    # NEW: Custom message
    message: Optional[str] = Field(default=None, max_length=1000, description="Custom invitation message")
    
    expiry_hours: int = Field(default=24, ge=1, le=168, description="Invitation expiry in hours (default 24)")
    
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
# ACCEPT INVITATION SCHEMA (Teacher)
# ============================================================

class AcceptInvitation(InvitationBase):
    """Schema for teacher accepting invitation."""
    
    token: str = Field(..., min_length=10, description="Invitation token")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    
    # NEW: Accept terms
    accept_terms: bool = Field(default=True, description="Accept terms and conditions")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username: alphanumeric and underscores only."""
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


# ============================================================
# RESEND INVITATION SCHEMA (Admin)
# ============================================================

class ResendInvitation(InvitationBase):
    """Schema for admin resending invitation."""
    
    invitation_id: int = Field(..., gt=0, description="Invitation ID")
    expiry_hours: int = Field(default=24, ge=1, le=168, description="New expiry in hours")
    
    # NEW: Custom message for resend
    message: Optional[str] = Field(default=None, max_length=1000, description="Custom message")


# ============================================================
# REVOKE INVITATION SCHEMA (Admin)
# ============================================================

class RevokeInvitation(InvitationBase):
    """Schema for admin revoking invitation."""
    
    invitation_id: int = Field(..., gt=0, description="Invitation ID")
    reason: str = Field(..., min_length=1, max_length=500, description="Revocation reason")


# ============================================================
# INVITATION RESPONSE SCHEMA
# ============================================================

class InvitationResponse(InvitationBase):
    """Schema for invitation record response."""
    
    id: int = Field(..., description="Invitation ID")
    email: str = Field(..., description="Teacher's email")
    full_name: str = Field(..., description="Teacher's full name")
    phone: Optional[str] = Field(default=None, description="Teacher's phone number")
    
    # NEW: Course information
    course_id: Optional[int] = Field(default=None, description="Course ID assigned")
    course_title: Optional[str] = Field(default=None, description="Course title")
    
    # NEW: Message
    message: Optional[str] = Field(default=None, description="Custom invitation message")
    
    invited_by: int = Field(..., description="Admin ID who sent invitation")
    invited_by_name: Optional[str] = Field(default=None, description="Admin name")
    
    token: str = Field(..., description="Invitation token")
    token_version: int = Field(default=1, description="Token version")
    
    status: str = Field(default="pending", description="Invitation status")
    accepted: bool = Field(default=False, description="Is invitation accepted?")
    accepted_at: Optional[datetime] = Field(default=None, description="Acceptance timestamp")
    
    # NEW: Accepted user
    accepted_user_id: Optional[int] = Field(default=None, description="User ID who accepted")
    accepted_user_name: Optional[str] = Field(default=None, description="User name who accepted")
    
    expires_at: datetime = Field(..., description="Expiry timestamp")
    expiry_hours: int = Field(default=24, description="Expiry hours")
    is_expired: bool = Field(..., description="Is invitation expired?")
    hours_until_expiry: float = Field(..., description="Hours until expiry")
    
    # NEW: Resend tracking
    resend_count: int = Field(default=0, description="Number of times resent")
    last_resend_at: Optional[datetime] = Field(default=None, description="Last resend timestamp")
    can_resend: bool = Field(default=True, description="Can be resent")
    
    # NEW: Revocation
    revoked_at: Optional[datetime] = Field(default=None, description="Revocation timestamp")
    revoked_by: Optional[int] = Field(default=None, description="Revoked by")
    revocation_reason: Optional[str] = Field(default=None, description="Revocation reason")
    
    # NEW: Reminder tracking
    reminder_count: int = Field(default=0, description="Number of reminders sent")
    last_reminder_at: Optional[datetime] = Field(default=None, description="Last reminder timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# INVITATION DETAIL RESPONSE (For teacher accepting)
# ============================================================

class InvitationDetailResponse(InvitationBase):
    """Schema for invitation detail when accepting."""
    
    id: int = Field(..., description="Invitation ID")
    email: str = Field(..., description="Teacher's email")
    full_name: str = Field(..., description="Teacher's full name")
    token: str = Field(..., description="Invitation token")
    
    # NEW: Course information
    course_id: Optional[int] = Field(default=None, description="Course ID assigned")
    course_title: Optional[str] = Field(default=None, description="Course title")
    
    # NEW: Message
    message: Optional[str] = Field(default=None, description="Custom invitation message")
    
    expires_at: datetime = Field(..., description="Expiry timestamp")
    is_expired: bool = Field(..., description="Is invitation expired?")
    accepted: bool = Field(..., description="Is already accepted?")
    invited_by: Optional[int] = Field(default=None, description="Admin ID who sent invitation")
    invited_by_name: Optional[str] = Field(default=None, description="Admin name")


# ============================================================
# INVITATION LIST REQUEST (Filters)
# ============================================================

class InvitationListRequest(InvitationBase):
    """Schema for invitation list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by name or email")
    status: Optional[InvitationStatusEnum] = Field(default=None, description="Filter by status")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# INVITATION LIST RESPONSE
# ============================================================

class InvitationListResponse(InvitationBase):
    """Schema for paginated invitation list response."""
    
    invitations: List[InvitationResponse] = Field(..., description="List of invitations")
    total: int = Field(..., description="Total number of invitations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# INVITATION STATUS SUMMARY (Admin Dashboard)
# ============================================================

class InvitationSummary(InvitationBase):
    """Schema for invitation summary on admin dashboard."""
    
    total_sent: int = Field(..., description="Total invitations sent")
    pending: int = Field(..., description="Pending invitations")
    accepted: int = Field(..., description="Accepted invitations")
    expired: int = Field(..., description="Expired invitations")
    revoked: int = Field(default=0, description="Revoked invitations")
    acceptance_rate: float = Field(..., description="Acceptance rate percentage")
    
    # NEW: Course breakdown
    course_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Invitations by course"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily invitation trends"
    )


# ============================================================
# BULK INVITATION SCHEMA
# ============================================================

class BulkInvitation(InvitationBase):
    """Schema for bulk teacher invitations."""
    
    emails: List[EmailStr] = Field(..., min_length=1, description="List of teacher emails")
    course_id: Optional[int] = Field(default=None, gt=0, description="Course ID to assign")
    expiry_hours: int = Field(default=24, ge=1, le=168, description="Expiry in hours")
    message: Optional[str] = Field(default=None, max_length=1000, description="Custom message")


class BulkInvitationResponse(InvitationBase):
    """Schema for bulk invitation response."""
    
    success_count: int = Field(..., description="Number of successful invitations")
    failed_count: int = Field(..., description="Number of failed invitations")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")
    created_invitations: List[InvitationResponse] = Field(
        default_factory=list,
        description="Created invitations"
    )


# ============================================================
# INVITATION REMINDER SCHEMA
# ============================================================

class InvitationReminder(InvitationBase):
    """Schema for sending invitation reminder."""
    
    invitation_id: int = Field(..., gt=0, description="Invitation ID")
    message: Optional[str] = Field(default=None, max_length=1000, description="Reminder message")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "InvitationStatusEnum",
    "InviteTeacher",
    "AcceptInvitation",
    "ResendInvitation",
    "RevokeInvitation",
    "InvitationResponse",
    "InvitationDetailResponse",
    "InvitationListRequest",
    "InvitationListResponse",
    "InvitationSummary",
    "BulkInvitation",
    "BulkInvitationResponse",
    "InvitationReminder",
]