# ============================================================
# AETHER LINK - USER SCHEMAS
# ============================================================

from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import Optional
from datetime import datetime
import re
from enum import Enum


# ============================================================
# USER ROLE ENUM
# ============================================================

class UserRoleEnum(str, Enum):
    """User role enumeration for schemas."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


# ============================================================
# USER RESPONSE SCHEMA
# ============================================================

class UserResponse(BaseModel):
    """Schema for user profile response (safe fields only)."""
    
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: str = Field(..., description="User's full name")
    phone: Optional[str] = Field(None, description="Phone number")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, description="User bio")
    role: UserRoleEnum = Field(..., description="User role")
    is_verified: bool = Field(..., description="Email verified?")
    is_active: bool = Field(..., description="Account active?")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    
    class Config:
        from_attributes = True


# ============================================================
# USER UPDATE SCHEMA
# ============================================================

class UserUpdate(BaseModel):
    """Schema for user profile update."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    profile_picture: Optional[str] = Field(None, max_length=500, description="Profile picture URL")
    
    @validator('phone')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (basic)."""
        if v is None:
            return v
        # Remove spaces, dashes, parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('profile_picture')
    def validate_profile_picture(cls, v: Optional[str]) -> Optional[str]:
        """Validate profile picture URL."""
        if v is None or v == "":
            return v
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Profile picture must be a valid URL')
        return v


# ============================================================
# ADMIN: USER ROLE UPDATE
# ============================================================

class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)."""
    
    role: UserRoleEnum = Field(..., description="New user role")


# ============================================================
# ADMIN: USER STATUS UPDATE
# ============================================================

class UserStatusUpdate(BaseModel):
    """Schema for updating user status (admin only)."""
    
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: Optional[bool] = Field(None, description="Whether user is verified")


# ============================================================
# ADMIN: USER LIST RESPONSE
# ============================================================

class UserListResponse(BaseModel):
    """Schema for user list response with pagination."""
    
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "UserRoleEnum",
    "UserResponse",
    "UserUpdate",
    "UserRoleUpdate",
    "UserStatusUpdate",
    "UserListResponse",
]