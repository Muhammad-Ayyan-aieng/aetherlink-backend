# ============================================================
# AETHER LINK - DEPENDENCIES
# ============================================================

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import time

from .database import get_db
from .security import decode_token, extract_user_id
from ..models.user import User, UserRole
from ..core.config import settings

# ============================================================
# OAUTH2 SCHEME
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True
)


# ============================================================
# CURRENT USER DEPENDENCIES
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    """
    try:
        # Extract user ID from token
        user_id = extract_user_id(token)
        
        # Get user from database
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact support."
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are verified.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email."
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_current_teacher_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a teacher or admin.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user


def get_current_teacher_only(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a teacher (not admin).
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user


# ============================================================
# RATE LIMITING DEPENDENCY (Basic - with Redis later)
# ============================================================

class RateLimiter:
    """
    Simple in-memory rate limiter.
    TODO: Replace with Redis-based implementation.
    """
    
    def __init__(self, requests: int = 10, period: int = 60):
        self.requests = requests
        self.period = period
        self._cache = {}
    
    def __call__(self, request: Request) -> bool:
        """
        Check if request is allowed.
        Returns True if allowed, raises HTTPException if rate limit exceeded.
        """
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        
        current_time = time.time()
        
        # Get existing data or create new
        data = self._cache.get(key, {"count": 0, "reset_time": current_time + self.period})
        
        # Reset if period expired
        if current_time > data["reset_time"]:
            data["count"] = 0
            data["reset_time"] = current_time + self.period
        
        # Increment count
        data["count"] += 1
        self._cache[key] = data
        
        # Check if limit exceeded
        if data["count"] > self.requests:
            # Clean up old entries periodically
            if len(self._cache) > 1000:
                self._clean_cache()
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests} requests per {self.period} seconds.",
                headers={
                    "X-RateLimit-Limit": str(self.requests),
                    "X-RateLimit-Remaining": str(0),
                    "X-RateLimit-Reset": str(int(data["reset_time"]))
                }
            )
        
        # Add rate limit headers
        remaining = self.requests - data["count"]
        headers = {
            "X-RateLimit-Limit": str(self.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(data["reset_time"]))
        }
        request.state.rate_limit_headers = headers
        
        return True
    
    def _clean_cache(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._cache.items()
            if current_time > data["reset_time"]
        ]
        for key in expired_keys:
            del self._cache[key]


# Create rate limiter instances for different endpoints
rate_limiter = RateLimiter(requests=settings.RATE_LIMIT_REQUESTS, period=settings.RATE_LIMIT_PERIOD)
auth_rate_limiter = RateLimiter(requests=5, period=60)  # Stricter for auth endpoints
admin_rate_limiter = RateLimiter(requests=20, period=60)  # More permissive for admins


# ============================================================
# GET CURRENT USER (For Websocket or Background Tasks)
# ============================================================

def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """
    Get user from token without FastAPI dependencies.
    Useful for websockets or background tasks.
    """
    try:
        user_id = extract_user_id(token)
        return db.query(User).filter(
            User.id == user_id,
            User.is_active == True,
            User.deleted_at.is_(None)
        ).first()
    except:
        return None


# ============================================================
# EXPOSE ALL DEPENDENCIES
# ============================================================

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "get_current_admin_user",
    "get_current_teacher_user",
    "get_current_teacher_only",
    "rate_limiter",
    "auth_rate_limiter",
    "admin_rate_limiter",
    "get_user_from_token",
    "oauth2_scheme",
]