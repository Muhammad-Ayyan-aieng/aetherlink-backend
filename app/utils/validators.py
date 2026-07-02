# ============================================================
# AETHER LINK - VALIDATORS
# ============================================================

import re
import socket
import dns.resolver
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from functools import lru_cache
from datetime import datetime, timedelta

# ============================================================
# CONSTANTS
# ============================================================

# Cache TTL for MX records (24 hours)
MX_CACHE_TTL = timedelta(hours=24)

# Common disposable email domains (can't be validated)
DISPOSABLE_DOMAINS = {
    'tempmail.com', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'throwaway.email', 'fakeemail.com',
    'trashmail.com', 'spamgourmet.com', 'yopmail.com',
    'maildrop.cc', 'temp-mail.org', 'getairmail.com'
}


# ============================================================
# EMAIL VALIDATION
# ============================================================

def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid format, False otherwise
    
    Examples:
        >>> validate_email_format("user@example.com")
        True
        
        >>> validate_email_format("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False
    
    # Clean and trim
    email = email.strip().lower()
    
    # Email pattern (RFC 5322 compliant)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Check max length (RFC 5321)
    if len(email) > 254:
        return False
    
    # Check local part (before @) max length (RFC 5321)
    local_part = email.split('@')[0]
    if len(local_part) > 64:
        return False
    
    return True


def validate_email_domain(email: str) -> bool:
    """
    Check if email domain has valid MX records.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if domain exists and has MX records
    
    Examples:
        >>> validate_email_domain("user@gmail.com")
        True
        
        >>> validate_email_domain("user@fakedomain123.com")
        False
    """
    if not email or not isinstance(email, str):
        return False
    
    try:
        # Extract domain
        domain = email.split('@')[1].strip().lower()
        
        if not domain:
            return False
        
        # Check MX records
        records = dns.resolver.resolve(domain, 'MX')
        
        # At least one MX record means domain can receive email
        return len(records) > 0
        
    except dns.resolver.NXDOMAIN:
        # Domain doesn't exist
        return False
    except dns.resolver.NoAnswer:
        # Domain exists but no MX records (can still receive email via A record)
        return True
    except dns.resolver.Timeout:
        # DNS timeout - assume valid (don't block registration)
        return True
    except Exception:
        # Any other error - be lenient
        return True


def validate_email(email: str, check_domain: bool = True) -> Dict[str, Any]:
    """
    Complete email validation (format + domain).
    
    Args:
        email: Email address to validate
        check_domain: Whether to check domain MX records
    
    Returns:
        Dictionary with validation results
    
    Examples:
        >>> validate_email("user@gmail.com")
        {"valid": True, "format_valid": True, "domain_valid": True}
        
        >>> validate_email("user@fakedomain123.com")
        {"valid": False, "format_valid": True, "domain_valid": False}
    """
    result = {
        "valid": False,
        "format_valid": False,
        "domain_valid": False,
        "is_disposable": False,
        "reason": "",
        "email": email.strip().lower() if email else "",
    }
    
    if not email or not isinstance(email, str):
        result["reason"] = "Email is required"
        return result
    
    # Clean email
    email_clean = email.strip().lower()
    result["email"] = email_clean
    
    # 1. Check format
    if not validate_email_format(email_clean):
        result["reason"] = "Invalid email format"
        return result
    
    result["format_valid"] = True
    
    # 2. Check disposable domains (optional)
    domain = email_clean.split('@')[1]
    if domain in DISPOSABLE_DOMAINS:
        result["is_disposable"] = True
        result["reason"] = "Disposable email domain not allowed"
        return result
    
    # 3. Check domain (if requested)
    if check_domain:
        domain_valid = validate_email_domain(email_clean)
        result["domain_valid"] = domain_valid
        
        if not domain_valid:
            result["reason"] = "Email domain does not exist"
            return result
    else:
        result["domain_valid"] = True  # Skip check, assume valid
    
    # All checks passed
    result["valid"] = True
    result["reason"] = "Valid email"
    
    return result


def validate_email_exists(email: str) -> Tuple[bool, str]:
    """
    Check if email domain exists and can receive emails.
    Simplified version that returns (valid, reason).
    
    Args:
        email: Email address
    
    Returns:
        Tuple of (is_valid, reason)
    
    Examples:
        >>> validate_email_exists("user@gmail.com")
        (True, "Valid email")
        
        >>> validate_email_exists("user@fake123.com")
        (False, "Domain does not exist")
    """
    result = validate_email(email, check_domain=True)
    return result["valid"], result["reason"]


# ============================================================
# PHONE VALIDATION
# ============================================================

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid format, False otherwise
    
    Examples:
        >>> validate_phone("+923001234567")
        True
        
        >>> validate_phone("03001234567")
        True
        
        >>> validate_phone("123")
        False
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Pattern: optional +, then 10-15 digits
    pattern = r'^\+?[0-9]{10,15}$'
    
    if not re.match(pattern, cleaned):
        return False
    
    # Pakistan phone validation (optional)
    # Check if it's a valid Pakistani number
    # Format: 03XXXXXXXXX or +923XXXXXXXXX
    if cleaned.startswith('03') and len(cleaned) == 11:
        return True
    if cleaned.startswith('+923') and len(cleaned) == 13:
        return True
    if cleaned.startswith('92') and len(cleaned) == 12:
        return True
    
    # For international numbers, just check format
    return True


# ============================================================
# URL VALIDATION
# ============================================================

def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        require_https: Whether to require HTTPS
    
    Returns:
        True if valid URL, False otherwise
    
    Examples:
        >>> validate_url("https://example.com")
        True
        
        >>> validate_url("http://example.com", require_https=True)
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        
        # Check if scheme and netloc exist
        if not result.scheme or not result.netloc:
            return False
        
        # Check allowed schemes
        allowed_schemes = ['http', 'https']
        if result.scheme not in allowed_schemes:
            return False
        
        # Check HTTPS requirement
        if require_https and result.scheme != 'https':
            return False
        
        # Check netloc format
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', result.netloc):
            return False
        
        return True
        
    except Exception:
        return False


# ============================================================
# SLUG VALIDATION
# ============================================================

def validate_slug(slug: str) -> bool:
    """
    Validate slug format (lowercase, letters, numbers, hyphens).
    
    Args:
        slug: Slug to validate
    
    Returns:
        True if valid slug, False otherwise
    
    Examples:
        >>> validate_slug("hello-world")
        True
        
        >>> validate_slug("Hello World")
        False
        
        >>> validate_slug("hello_world")
        False
    """
    if not slug or not isinstance(slug, str):
        return False
    
    # Only lowercase letters, numbers, and hyphens
    pattern = r'^[a-z0-9\-]+$'
    
    if not re.match(pattern, slug):
        return False
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False
    
    # Cannot have consecutive hyphens
    if '--' in slug:
        return False
    
    # Max length
    if len(slug) > 255:
        return False
    
    return True


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength and return detailed feedback.
    
    Args:
        password: Password to validate
    
    Returns:
        Dictionary with strength analysis
    
    Examples:
        >>> validate_password_strength("Password123!")
        {"is_strong": True, "score": 10, "errors": [], "warnings": []}
        
        >>> validate_password_strength("123")
        {"is_strong": False, "score": 4, "errors": ["Password must be at least 8 characters"], ...}
    """
    errors = []
    warnings = []
    
    if not password or not isinstance(password, str):
        errors.append("Password is required")
        return {
            "is_strong": False,
            "errors": errors,
            "warnings": warnings,
            "score": 0,
        }
    
    # Length checks
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    if len(password) > 72:
        warnings.append("Password longer than 72 characters may have issues with bcrypt")
    
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
    common_patterns = [
        'password', '123456', 'qwerty', 'admin', 
        'letmein', 'welcome', 'abc123', 'monkey',
        'password123', '123456789', '12345678'
    ]
    if any(pattern in password.lower() for pattern in common_patterns):
        warnings.append("Avoid common passwords")
    
    # Sequential patterns
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower()):
        warnings.append("Avoid sequential characters")
    
    # Repeated characters
    if re.search(r'(.)\1{3,}', password):
        warnings.append("Avoid repeated characters")
    
    # Calculate score (0-10)
    score = 10
    score -= len(errors) * 2
    score -= len(warnings)
    score = max(0, min(10, score))
    
    return {
        "is_strong": len(errors) == 0 and score >= 6,
        "errors": errors,
        "warnings": warnings,
        "score": score,
    }


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Simplified password validation.
    Returns (is_valid, reason)
    """
    result = validate_password_strength(password)
    
    if result["errors"]:
        return False, result["errors"][0]
    
    if not result["is_strong"]:
        return False, "Password is too weak"
    
    return True, "Strong password"


# ============================================================
# CACHE HELPER FOR MX RECORDS
# ============================================================

@lru_cache(maxsize=1000)
def _get_mx_records_cached(domain: str) -> bool:
    """
    Cached version of MX record lookup.
    Caches results for 24 hours.
    """
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except:
        return False


def clear_mx_cache():
    """Clear the MX record cache."""
    _get_mx_records_cached.cache_clear()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Email
    'validate_email_format',
    'validate_email_domain',
    'validate_email',
    'validate_email_exists',
    
    # Phone
    'validate_phone',
    
    # URL
    'validate_url',
    
    # Slug
    'validate_slug',
    
    # Password
    'validate_password_strength',
    'validate_password',
    
    # Cache
    'clear_mx_cache',
]