# ============================================================
# AETHER LINK - AUTH SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class MFAType(str, Enum):
    """MFA type enumeration."""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup_code"


class DeviceType(str, Enum):
    """Device type enumeration."""
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    OTHER = "other"


# ============================================================
# BASE SCHEMA
# ============================================================

class AuthBase(BaseModel):
    """Base auth schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# REGISTER SCHEMA
# ============================================================

class RegisterRequest(AuthBase):
    """Schema for user registration."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Phone number")
    
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
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        
        # Optional: Check for at least one uppercase, lowercase, digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


# ============================================================
# LOGIN SCHEMA
# ============================================================

class LoginRequest(AuthBase):
    """Schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Remember me")
    device_name: Optional[str] = Field(default=None, max_length=100, description="Device name")
    device_type: Optional[DeviceType] = Field(default=DeviceType.OTHER, description="Device type")


class LoginResponse(AuthBase):
    """Schema for login response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiry in seconds")
    user: Dict[str, Any] = Field(..., description="User information")
    requires_mfa: bool = Field(default=False, description="MFA required")
    mfa_type: Optional[str] = Field(default=None, description="MFA type")
    session_id: Optional[int] = Field(default=None, description="Session ID")


# ============================================================
# MFA SCHEMAS
# ============================================================

class MFASetupRequest(AuthBase):
    """Schema for MFA setup request."""
    
    mfa_type: MFAType = Field(..., description="MFA type")
    phone: Optional[str] = Field(default=None, description="Phone number for SMS MFA")
    email: Optional[EmailStr] = Field(default=None, description="Email for Email MFA")


class MFASetupResponse(AuthBase):
    """Schema for MFA setup response."""
    
    secret: Optional[str] = Field(default=None, description="TOTP secret")
    qr_code_url: Optional[str] = Field(default=None, description="QR code URL")
    backup_codes: Optional[List[str]] = Field(default=None, description="Backup codes")
    message: str = Field(..., description="Setup message")


class MFAVerifyRequest(AuthBase):
    """Schema for MFA verification request."""
    
    code: str = Field(..., description="MFA code")
    mfa_type: Optional[MFAType] = Field(default=None, description="MFA type")
    remember_device: bool = Field(default=False, description="Remember this device")


class MFAVerifyResponse(AuthBase):
    """Schema for MFA verification response."""
    
    success: bool = Field(..., description="Verification success")
    access_token: Optional[str] = Field(default=None, description="JWT access token")
    refresh_token: Optional[str] = Field(default=None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(default=None, description="Token expiry in seconds")
    message: str = Field(..., description="Verification message")


class MFADisableRequest(AuthBase):
    """Schema for MFA disable request."""
    
    code: str = Field(..., description="MFA code to disable")


# ============================================================
# TOKEN SCHEMAS
# ============================================================

class TokenResponse(AuthBase):
    """Schema for JWT token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiry in seconds")


class RefreshTokenRequest(AuthBase):
    """Schema for refresh token request."""
    
    refresh_token: str = Field(..., description="Refresh token")


class TokenData(AuthBase):
    """Schema for token payload data."""
    
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str = Field(..., description="JWT ID")
    session_id: Optional[int] = Field(default=None, description="Session ID")


class TokenIntrospectResponse(AuthBase):
    """Schema for token introspection response."""
    
    active: bool = Field(..., description="Token active status")
    user_id: Optional[int] = Field(default=None, description="User ID")
    email: Optional[str] = Field(default=None, description="User email")
    role: Optional[str] = Field(default=None, description="User role")
    exp: Optional[int] = Field(default=None, description="Expiration timestamp")
    iat: Optional[int] = Field(default=None, description="Issued at timestamp")
    jti: Optional[str] = Field(default=None, description="JWT ID")
    client_id: Optional[str] = Field(default=None, description="Client ID")
    scope: Optional[str] = Field(default=None, description="Token scope")


# ============================================================
# PASSWORD SCHEMAS
# ============================================================

class PasswordChangeRequest(AuthBase):
    """Schema for password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
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


class ForgotPasswordRequest(AuthBase):
    """Schema for forgot password request."""
    
    email: EmailStr = Field(..., description="User email")


class ResetPasswordRequest(AuthBase):
    """Schema for reset password confirmation."""
    
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
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
# EMAIL VERIFICATION
# ============================================================

class VerifyEmailRequest(AuthBase):
    """Schema for email verification request."""
    
    email: EmailStr = Field(..., description="Email to verify")


class VerifyEmailConfirmRequest(AuthBase):
    """Schema for email verification confirmation."""
    
    token: str = Field(..., description="Verification token")


class ResendVerificationRequest(AuthBase):
    """Schema for resend verification email."""
    
    email: EmailStr = Field(..., description="Email to resend verification")


# ============================================================
# LOGOUT SCHEMAS
# ============================================================

class LogoutRequest(AuthBase):
    """Schema for logout request."""
    
    refresh_token: Optional[str] = Field(default=None, description="Refresh token to revoke")
    session_id: Optional[int] = Field(default=None, description="Session ID to revoke")


class LogoutAllDevicesRequest(AuthBase):
    """Schema for logout all devices request."""
    
    pass  # No body needed


class LogoutResponse(AuthBase):
    """Schema for logout response."""
    
    message: str = Field(default="Successfully logged out", description="Logout message")
    revoked_sessions: Optional[int] = Field(default=None, description="Number of revoked sessions")


# ============================================================
# SESSION SCHEMAS
# ============================================================

class SessionInfo(AuthBase):
    """Schema for session information."""
    
    id: int = Field(..., description="Session ID")
    device_name: Optional[str] = Field(default=None, description="Device name")
    device_type: str = Field(..., description="Device type")
    browser_name: Optional[str] = Field(default=None, description="Browser name")
    os_name: Optional[str] = Field(default=None, description="Operating system")
    ip_address: Optional[str] = Field(default=None, description="IP address")
    country: Optional[str] = Field(default=None, description="Country")
    city: Optional[str] = Field(default=None, description="City")
    is_current: bool = Field(default=False, description="Is current session")
    is_active: bool = Field(default=True, description="Is session active")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity time")
    idle_minutes: Optional[float] = Field(default=None, description="Idle time in minutes")
    expires_at: datetime = Field(..., description="Session expiry time")


class SessionListResponse(AuthBase):
    """Schema for session list response."""
    
    sessions: List[SessionInfo] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total sessions")


class RevokeSessionRequest(AuthBase):
    """Schema for revoke session request."""
    
    session_id: int = Field(..., description="Session ID to revoke")


# ============================================================
# DEVICE TRUST SCHEMAS
# ============================================================

class DeviceTrustRequest(AuthBase):
    """Schema for device trust request."""
    
    device_fingerprint: str = Field(..., description="Device fingerprint")
    device_name: Optional[str] = Field(default=None, description="Device name")
    device_type: Optional[DeviceType] = Field(default=DeviceType.OTHER, description="Device type")
    trust_duration_days: Optional[int] = Field(default=30, description="Trust duration in days")


class DeviceTrustResponse(AuthBase):
    """Schema for device trust response."""
    
    is_trusted: bool = Field(..., description="Is device trusted")
    trusted_until: Optional[datetime] = Field(default=None, description="Trust expiry")
    message: str = Field(..., description="Trust message")


# ============================================================
# RATE LIMIT SCHEMAS
# ============================================================

class RateLimitStatus(AuthBase):
    """Schema for rate limit status."""
    
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset: int = Field(..., description="Reset timestamp")
    retry_after: Optional[int] = Field(default=None, description="Retry after seconds")


# ============================================================
# ACCOUNT LOCKOUT SCHEMAS
# ============================================================

class AccountLockoutStatus(AuthBase):
    """Schema for account lockout status."""
    
    is_locked: bool = Field(..., description="Is account locked")
    locked_until: Optional[datetime] = Field(default=None, description="Locked until")
    remaining_attempts: int = Field(..., description="Remaining login attempts before lockout")
    message: Optional[str] = Field(default=None, description="Lockout message")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Enums
    "MFAType",
    "DeviceType",
    
    # Base
    "AuthBase",
    
    # Register
    "RegisterRequest",
    
    # Login
    "LoginRequest",
    "LoginResponse",
    
    # MFA
    "MFASetupRequest",
    "MFASetupResponse",
    "MFAVerifyRequest",
    "MFAVerifyResponse",
    "MFADisableRequest",
    
    # Token
    "TokenResponse",
    "RefreshTokenRequest",
    "TokenData",
    "TokenIntrospectResponse",
    
    # Password
    "PasswordChangeRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    
    # Email Verification
    "VerifyEmailRequest",
    "VerifyEmailConfirmRequest",
    "ResendVerificationRequest",
    
    # Logout
    "LogoutRequest",
    "LogoutAllDevicesRequest",
    "LogoutResponse",
    
    # Session
    "SessionInfo",
    "SessionListResponse",
    "RevokeSessionRequest",
    
    # Device Trust
    "DeviceTrustRequest",
    "DeviceTrustResponse",
    
    # Rate Limit
    "RateLimitStatus",
    
    # Account Lockout
    "AccountLockoutStatus",
]