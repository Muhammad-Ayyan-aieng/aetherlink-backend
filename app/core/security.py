# ============================================================
# AETHER LINK - SECURITY
# ============================================================

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import re
from fastapi import HTTPException, status
from passlib.context import CryptContext

from .config import settings


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    Handles bcrypt's 72-byte limit by truncating if necessary.
    """
    # Enforce minimum length
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    # Enforce maximum length (72 bytes for bcrypt)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password[:72]  # Truncate to 72 bytes
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    Uses constant-time comparison to prevent timing attacks.
    """
    try:
        # Enforce max length before verification
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password[:72]
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Return False on any error (prevents user enumeration)
        return False


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed feedback.
    """
    errors = []
    warnings = []
    
    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    
    # Complexity checks
    if not re.search(r'[A-Z]', password):
        warnings.append("Include at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        warnings.append("Include at least one lowercase letter")
    if not re.search(r'\d', password):
        warnings.append("Include at least one number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        warnings.append("Include at least one special character")
    
    # Common patterns check
    common_patterns = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome']
    if any(pattern in password.lower() for pattern in common_patterns):
        warnings.append("Avoid common passwords")
    
    return {
        "is_strong": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "score": max(0, 10 - len(errors) * 2 - len(warnings))
    }


# ============================================================
# JWT TOKENS
# ============================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.
    """
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises HTTPException if token is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        error_messages = {
            "Signature verification failed": "Invalid token signature",
            "Signature has expired": "Token has expired",
            "Invalid audience": "Invalid token audience",
            "Invalid issuer": "Invalid token issuer",
            "Invalid algorithm": "Invalid token algorithm"
        }
        
        error_msg = error_messages.get(str(e), "Invalid authentication token")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without raising an exception.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        exp = payload.get("exp")
        if exp:
            return datetime.utcnow() > datetime.utcfromtimestamp(exp)
        return True
    except:
        return True


def get_token_type(token: str) -> Optional[str]:
    """
    Get the type of token (access or refresh).
    """
    try:
        payload = decode_token(token)
        return payload.get("type")
    except:
        return None


def extract_user_id(token: str) -> int:
    """
    Extract user ID from a validated token.
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return int(user_id)


# ============================================================
# TOKEN BLACKLIST (Future - with Redis)
# ============================================================

# TODO: Implement token blacklist with Redis for logout
# def blacklist_token(token: str) -> None:
#     """Add token to blacklist."""
#     pass
#
# def is_token_blacklisted(token: str) -> bool:
#     """Check if token is blacklisted."""
#     return False


# ============================================================
# SECURE RANDOM GENERATORS
# ============================================================

import secrets
import string


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a secure random password.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))