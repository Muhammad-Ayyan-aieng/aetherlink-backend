# ============================================================
# AETHER LINK - AUTH SCHEMAS
# ============================================================

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ============================================================
# REGISTER SCHEMA
# ============================================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 characters)")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username: alphanumeric and underscores only."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must be less than 72 characters')
        
        # Optional: Check for at least one uppercase, lowercase, digit
        # if not re.search(r'[A-Z]', v):
        #     raise ValueError('Password must contain at least one uppercase letter')
        # if not re.search(r'[a-z]', v):
        #     raise ValueError('Password must contain at least one lowercase letter')
        # if not re.search(r'\d', v):
        #     raise ValueError('Password must contain at least one number')
        
        return v


# ============================================================
# LOGIN SCHEMA
# ============================================================

class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


# ============================================================
# TOKEN SCHEMAS
# ============================================================

class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class RefreshToken(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str = Field(..., description="Refresh token")


class TokenData(BaseModel):
    """Schema for token payload data."""
    
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiration timestamp")


# ============================================================
# PASSWORD SCHEMAS
# ============================================================

class PasswordChange(BaseModel):
    """Schema for password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=72, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must be less than 72 characters')
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=72, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must be less than 72 characters')
        return v


# ============================================================
# EMAIL VERIFICATION
# ============================================================

class EmailVerification(BaseModel):
    """Schema for email verification."""
    
    email: EmailStr = Field(..., description="Email to verify")


class EmailVerificationConfirm(BaseModel):
    """Schema for email verification confirmation."""
    
    token: str = Field(..., description="Verification token")


# ============================================================
# LOGOUT
# ============================================================

class LogoutResponse(BaseModel):
    """Schema for logout response."""
    
    message: str = Field(default="Successfully logged out", description="Logout message")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "RefreshToken",
    "TokenData",
    "PasswordChange",
    "PasswordReset",
    "PasswordResetConfirm",
    "EmailVerification",
    "EmailVerificationConfirm",
    "LogoutResponse",
]