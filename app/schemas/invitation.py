# ============================================================
# AETHER LINK - INVITATION SCHEMAS
# ============================================================

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ============================================================
# INVITE TEACHER SCHEMA (Admin)
# ============================================================

class InviteTeacher(BaseModel):
    """Schema for admin inviting a teacher."""
    
    email: EmailStr = Field(..., description="Teacher's email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="Teacher's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Teacher's phone number")
    expiry_days: int = Field(7, ge=1, le=30, description="Invitation expiry in days")
    
    @validator('phone')
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

class AcceptInvitation(BaseModel):
    """Schema for teacher accepting invitation."""
    
    token: str = Field(..., min_length=10, description="Invitation token")
    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 characters)")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    
    @validator('username')
    def validate_username(cls, v: str) -> str:
        """Validate username: alphanumeric and underscores only."""
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must be less than 72 characters')
        return v


# ============================================================
# RESEND INVITATION SCHEMA (Admin)
# ============================================================

class ResendInvitation(BaseModel):
    """Schema for admin resending invitation."""
    
    invitation_id: int = Field(..., gt=0, description="Invitation ID")
    expiry_days: int = Field(7, ge=1, le=30, description="New expiry in days")


# ============================================================
# INVITATION RESPONSE SCHEMA
# ============================================================

class InvitationResponse(BaseModel):
    """Schema for invitation record response."""
    
    id: int = Field(..., description="Invitation ID")
    email: str = Field(..., description="Teacher's email")
    full_name: str = Field(..., description="Teacher's full name")
    phone: Optional[str] = Field(None, description="Teacher's phone number")
    
    invited_by: int = Field(..., description="Admin ID who sent invitation")
    invited_by_name: Optional[str] = Field(None, description="Admin name")
    
    token: str = Field(..., description="Invitation token")
    accepted: bool = Field(False, description="Is invitation accepted?")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")
    
    expires_at: datetime = Field(..., description="Expiry timestamp")
    is_expired: bool = Field(..., description="Is invitation expired?")
    days_until_expiry: int = Field(..., description="Days until expiry")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


# ============================================================
# INVITATION DETAIL RESPONSE (For teacher accepting)
# ============================================================

class InvitationDetailResponse(BaseModel):
    """Schema for invitation detail when accepting."""
    
    email: str = Field(..., description="Teacher's email")
    full_name: str = Field(..., description="Teacher's full name")
    token: str = Field(..., description="Invitation token")
    expires_at: datetime = Field(..., description="Expiry timestamp")
    is_expired: bool = Field(..., description="Is invitation expired?")
    accepted: bool = Field(..., description="Is already accepted?")
    
    class Config:
        from_attributes = True


# ============================================================
# INVITATION LIST RESPONSE
# ============================================================

class InvitationListResponse(BaseModel):
    """Schema for paginated invitation list response."""
    
    invitations: List[InvitationResponse] = Field(..., description="List of invitations")
    total: int = Field(..., description="Total number of invitations")
    pending_count: int = Field(..., description="Pending invitations")
    accepted_count: int = Field(..., description="Accepted invitations")
    expired_count: int = Field(..., description="Expired invitations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# INVITATION STATUS SUMMARY (Admin Dashboard)
# ============================================================

class InvitationSummary(BaseModel):
    """Schema for invitation summary on admin dashboard."""
    
    total_sent: int = Field(..., description="Total invitations sent")
    pending: int = Field(..., description="Pending invitations")
    accepted: int = Field(..., description="Accepted invitations")
    expired: int = Field(..., description="Expired invitations")
    acceptance_rate: float = Field(..., description="Acceptance rate percentage")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "InviteTeacher",
    "AcceptInvitation",
    "ResendInvitation",
    "InvitationResponse",
    "InvitationDetailResponse",
    "InvitationListResponse",
    "InvitationSummary",
]