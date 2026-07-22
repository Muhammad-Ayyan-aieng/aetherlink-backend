# ============================================================
# AETHER LINK - USER SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
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
    CLIENT = "client"        # NEW: Software House client
    DEVELOPER = "developer"  # NEW: Software House developer


# ============================================================
# BASE SCHEMA
# ============================================================

class UserBase(BaseModel):
    """Base user schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# USER RESPONSE SCHEMA
# ============================================================

class UserResponse(UserBase):
    """Schema for user profile response (safe fields only)."""
    
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: str = Field(..., description="User's full name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    profile_picture: Optional[str] = Field(default=None, description="Profile picture URL")
    bio: Optional[str] = Field(default=None, description="User bio")
    role: UserRoleEnum = Field(..., description="User role")
    
    # NEW: Student ID (for students)
    student_id: Optional[str] = Field(default=None, description="Student ID (AETH-XXXXX)")
    
    is_verified: bool = Field(..., description="Email verified?")
    is_active: bool = Field(..., description="Account active?")
    last_login: Optional[datetime] = Field(default=None, description="Last login time")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: Optional[datetime] = Field(default=None, description="Last update time")


# ============================================================
# USER DETAILED RESPONSE (For user's own profile)
# ============================================================

class UserProfileResponse(UserResponse):
    """Detailed user profile response (includes more fields)."""
    
    phone: Optional[str] = Field(default=None, description="Phone number")
    bio: Optional[str] = Field(default=None, description="User bio")
    last_login: Optional[datetime] = Field(default=None, description="Last login time")
    
    # NEW: Account statistics
    total_courses_enrolled: Optional[int] = Field(default=0, description="Total courses enrolled")
    total_courses_completed: Optional[int] = Field(default=0, description="Total courses completed")
    total_certificates: Optional[int] = Field(default=0, description="Total certificates earned")


# ============================================================
# USER ADMIN RESPONSE (Full access for admin)
# ============================================================

class UserAdminResponse(UserResponse):
    """Admin view of user (includes sensitive fields)."""
    
    failed_login_attempts: int = Field(default=0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(default=None, description="Account locked until")
    deleted_at: Optional[datetime] = Field(default=None, description="Soft delete timestamp")
    
    # NEW: IP tracking
    last_login_ip: Optional[str] = Field(default=None, description="Last login IP address")
    created_ip: Optional[str] = Field(default=None, description="Account creation IP address")


# ============================================================
# USER UPDATE SCHEMA
# ============================================================

class UserUpdate(UserBase):
    """Schema for user profile update."""
    
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(default=None, max_length=500, description="User bio")
    profile_picture: Optional[str] = Field(default=None, max_length=500, description="Profile picture URL")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (basic)."""
        if v is None or v == "":
            return v
        # Remove spaces, dashes, parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('profile_picture')
    @classmethod
    def validate_profile_picture(cls, v: Optional[str]) -> Optional[str]:
        """Validate profile picture URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Profile picture must be a valid URL')
        return v


# ============================================================
# ADMIN: USER ROLE UPDATE
# ============================================================

class UserRoleUpdate(UserBase):
    """Schema for updating user role (admin only)."""
    
    role: UserRoleEnum = Field(..., description="New user role")
    reason: Optional[str] = Field(default=None, description="Reason for role change")


# ============================================================
# ADMIN: USER STATUS UPDATE
# ============================================================

class UserStatusUpdate(UserBase):
    """Schema for updating user status (admin only)."""
    
    is_active: Optional[bool] = Field(default=None, description="Whether user account is active")
    is_verified: Optional[bool] = Field(default=None, description="Whether user is verified")
    reason: Optional[str] = Field(default=None, description="Reason for status change")


# ============================================================
# ADMIN: USER LOCK/UNLOCK
# ============================================================

class UserLockRequest(UserBase):
    """Schema for locking/unlocking user account."""
    
    lock: bool = Field(..., description="True to lock, False to unlock")
    reason: Optional[str] = Field(default=None, description="Reason for lock/unlock")
    duration_minutes: Optional[int] = Field(default=30, description="Lock duration in minutes")


# ============================================================
# USER LIST REQUEST (Filters)
# ============================================================

class UserListRequest(UserBase):
    """Schema for user list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by name or email")
    role: Optional[UserRoleEnum] = Field(default=None, description="Filter by role")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    is_verified: Optional[bool] = Field(default=None, description="Filter by verified status")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# USER LIST RESPONSE
# ============================================================

class UserListResponse(UserBase):
    """Schema for user list response with pagination."""
    
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# ADMIN: USER LIST RESPONSE (Full access)
# ============================================================

class AdminUserListResponse(UserBase):
    """Admin user list response with full details."""
    
    users: List[UserAdminResponse] = Field(..., description="List of users with full details")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# BULK USER OPERATIONS
# ============================================================

class BulkUserActionRequest(UserBase):
    """Schema for bulk user operations."""
    
    user_ids: List[int] = Field(..., description="List of user IDs")
    action: str = Field(..., description="Action to perform (activate, deactivate, verify, delete)")


class BulkUserActionResponse(UserBase):
    """Schema for bulk user operation response."""
    
    success_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")


# ============================================================
# USER STATISTICS
# ============================================================

class UserStatistics(UserBase):
    """Schema for user statistics."""
    
    total_users: int = Field(..., description="Total users")
    active_users: int = Field(..., description="Active users")
    inactive_users: int = Field(..., description="Inactive users")
    verified_users: int = Field(..., description="Verified users")
    unverified_users: int = Field(..., description="Unverified users")
    students: int = Field(..., description="Total students")
    teachers: int = Field(..., description="Total teachers")
    admins: int = Field(..., description="Total admins")
    clients: int = Field(..., description="Total clients")
    developers: int = Field(..., description="Total developers")
    new_users_today: int = Field(..., description="New users today")
    new_users_this_week: int = Field(..., description="New users this week")
    new_users_this_month: int = Field(..., description="New users this month")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "UserRoleEnum",
    "UserBase",
    "UserResponse",
    "UserProfileResponse",
    "UserAdminResponse",
    "UserUpdate",
    "UserRoleUpdate",
    "UserStatusUpdate",
    "UserLockRequest",
    "UserListRequest",
    "UserListResponse",
    "AdminUserListResponse",
    "BulkUserActionRequest",
    "BulkUserActionResponse",
    "UserStatistics",
]