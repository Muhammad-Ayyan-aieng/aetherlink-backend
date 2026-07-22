# ============================================================
# AETHER LINK - TOKEN SCHEMAS
# ============================================================

from typing import Optional
from pydantic import Field
from datetime import datetime

from .common import BaseSchema


# ============================================================
# TOKEN SCHEMAS
# ============================================================

class TokenResponse(BaseSchema):
    """Token response schema."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class RefreshTokenRequest(BaseSchema):
    """Refresh token request schema."""
    refresh_token: str = Field(..., description="Refresh token")


class TokenPayload(BaseSchema):
    """JWT token payload schema."""
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiry timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str = Field(..., description="JWT ID")


class TokenInfoResponse(BaseSchema):
    """Token information response."""
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expires in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiry in seconds")