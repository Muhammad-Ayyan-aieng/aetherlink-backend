# ============================================================
# AETHER LINK - PASSWORD RESET MODEL
# ============================================================
# Purpose: Track password reset requests with security features
# Security: Tokens are hashed, one-time use, time-limited
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
import hashlib
import secrets

from ..core.database import Base


class ResetRequestStatus(str, enum.Enum):
    """Password reset request status."""
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PasswordReset(Base):
    __tablename__ = "password_reset_requests"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # TOKEN DATA (Hashed for security)
    # ============================================================
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    # We store only the hash, never the plain token
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # When token was used
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # When token was revoked (admin action)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(String(20), default=ResetRequestStatus.PENDING.value, nullable=False, index=True)
    
    # ============================================================
    # REQUEST CONTEXT (Security Tracking)
    # ============================================================
    # IP address of the requester
    ip_address = Column(String(100), nullable=True)
    
    # User agent of the requester
    user_agent = Column(Text, nullable=True)
    
    # Device fingerprint (optional)
    device_id = Column(String(255), nullable=True)
    
    # Location info (geo-ip)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # ============================================================
    # SUCCESS/FALLBACK TRACKING
    # ============================================================
    # Whether the reset was successful
    was_successful = Column(Boolean, default=False, nullable=False)
    
    # If failed, why? (optional)
    failure_reason = Column(String(100), nullable=True)
    
    # New password was set (we don't store the password, just flag)
    password_changed = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # USER RESPONSE TRACKING
    # ============================================================
    # How many times the user requested a reset (within a period)
    request_count = Column(Integer, default=1, nullable=False)
    
    # Last time this user requested a reset
    last_request_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    # Example: {"browser": "Chrome", "os": "Windows", "referrer": "https://..."}
    
    # ============================================================
    # ADMIN NOTES
    # ============================================================
    admin_notes = Column(Text, nullable=True)  # For support/admin reference
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    user = relationship(
        "User",
        back_populates="password_reset_requests",
        foreign_keys=[user_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<PasswordReset {self.id} - User {self.user_id} - {self.status}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_pending(self) -> bool:
        """Check if reset request is pending (valid, not used/expired)."""
        return (
            self.status == ResetRequestStatus.PENDING.value
            and self.expires_at > func.now()
            and self.used_at is None
        )
    
    @property
    def is_used(self) -> bool:
        """Check if reset request was already used."""
        return self.status == ResetRequestStatus.USED.value
    
    @property
    def is_expired(self) -> bool:
        """Check if reset request has expired."""
        return self.expires_at <= func.now()
    
    @property
    def is_revoked(self) -> bool:
        """Check if reset request was revoked by admin."""
        return self.status == ResetRequestStatus.REVOKED.value
    
    @property
    def age_minutes(self) -> float:
        """Get request age in minutes."""
        if self.created_at is None:
            return 0.0
        delta = func.now() - self.created_at
        return delta.total_seconds() / 60
    
    @property
    def expires_in_minutes(self) -> float:
        """Get minutes until expiry."""
        if self.expires_at is None:
            return 0.0
        delta = self.expires_at - func.now()
        return max(0.0, delta.total_seconds() / 60)
    
    @property
    def is_rate_limited(self) -> bool:
        """Check if user is rate-limited for reset requests."""
        # Rate limit: 3 requests per 24 hours
        if self.request_count >= 3 and self.last_request_at:
            hours_since_last = (func.now() - self.last_request_at).total_seconds() / 3600
            if hours_since_last < 24:
                return True
        return False
    
    @property
    def can_retry(self) -> bool:
        """Check if user can request another reset."""
        if self.is_expired and not self.is_used:
            return True
        return False
    
    @property
    def request_context(self) -> dict:
        """Get request context as dictionary."""
        return {
            "ip_address": self.ip_address,
            "country": self.country,
            "city": self.city,
            "device_id": self.device_id,
            "user_agent": self.user_agent,
        }
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def mark_used(self, success: bool = True) -> None:
        """
        Mark this reset request as used.
        
        Args:
            success: Whether the reset was successful
        """
        self.status = ResetRequestStatus.USED.value
        self.used_at = func.now()
        self.was_successful = success
        
        if success:
            self.password_changed = True
    
    def mark_expired(self) -> None:
        """Mark this reset request as expired."""
        if self.is_pending:
            self.status = ResetRequestStatus.EXPIRED.value
    
    def revoke(self, admin_notes: str = None) -> None:
        """
        Revoke this reset request (admin action).
        
        Args:
            admin_notes: Notes from admin for revocation
        """
        self.status = ResetRequestStatus.REVOKED.value
        self.revoked_at = func.now()
        if admin_notes:
            self.admin_notes = admin_notes
    
    def increment_request_count(self) -> None:
        """Increment the request count for rate limiting."""
        self.request_count += 1
        self.last_request_at = func.now()
    
    def reset_request_count(self) -> None:
        """Reset the request count (after successful reset or after cooldown)."""
        self.request_count = 0
        self.last_request_at = None
    
    def set_failure_reason(self, reason: str) -> None:
        """Set failure reason for tracking."""
        self.failure_reason = reason
    
    def set_request_context(self, ip_address: str, user_agent: str, **kwargs) -> None:
        """Set request context information."""
        self.ip_address = ip_address
        self.user_agent = user_agent
        
        if "device_id" in kwargs:
            self.device_id = kwargs["device_id"]
        if "country" in kwargs:
            self.country = kwargs["country"]
        if "city" in kwargs:
            self.city = kwargs["city"]
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert reset request to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "is_pending": self.is_pending,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "expires_in_minutes": self.expires_in_minutes,
            "age_minutes": self.age_minutes,
            "request_count": self.request_count,
            "is_rate_limited": self.is_rate_limited,
            "request_context": self.request_context,
            "was_successful": self.was_successful,
            "password_changed": self.password_changed,
        }
        
        if include_sensitive:
            data.update({
                "token_hash": self.token_hash,
                "used_at": self.used_at.isoformat() if self.used_at else None,
                "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
                "failure_reason": self.failure_reason,
                "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
                "admin_notes": self.admin_notes,
                "metadata": self.metadata,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing reset request data (safe for API responses)."""
        return {
            "id": self.id,
            "status": self.status,
            "is_pending": self.is_pending,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_in_minutes": self.expires_in_minutes,
            "can_retry": self.can_retry,
        }
    
    # ============================================================
    # CLASS METHODS
    # ============================================================
    
    @classmethod
    def generate_token(cls, length: int = 64) -> str:
        """
        Generate a cryptographically secure token.
        
        Args:
            length: Length of the token in characters (default: 64)
        
        Returns:
            Secure random hex string
        """
        return secrets.token_hex(length // 2)  # hex gives 2 chars per byte
    
    @classmethod
    def hash_token(cls, token: str) -> str:
        """
        Hash a token for storage.
        
        Args:
            token: The plain token to hash
        
        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @classmethod
    def create_request(
        cls,
        user_id: int,
        token: str,
        expires_in_minutes: int = 60,
        ip_address: str = None,
        user_agent: str = None,
        device_id: str = None,
        country: str = None,
        city: str = None,
        **kwargs
    ) -> "PasswordReset":
        """
        Create a new password reset request.
        
        Args:
            user_id: User ID
            token: Plain token (will be hashed for storage)
            expires_in_minutes: Token expiry in minutes (default: 60)
            ip_address: IP address of the requester
            user_agent: User agent of the requester
            device_id: Device fingerprint
            country: Country from geo-ip
            city: City from geo-ip
            **kwargs: Additional metadata
        
        Returns:
            PasswordReset instance
        """
        token_hash = cls.hash_token(token)
        expires_at = func.now() + func.interval(f'{expires_in_minutes} minutes')
        
        return cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            country=country,
            city=city,
            status=ResetRequestStatus.PENDING.value,
            metadata=kwargs.get("metadata"),
        )
    
    @classmethod
    def verify_token(cls, token: str, token_hash: str) -> bool:
        """
        Verify if a token matches its hash.
        
        Args:
            token: The plain token provided by user
            token_hash: The stored token hash
        
        Returns:
            True if token matches, False otherwise
        """
        return cls.hash_token(token) == token_hash


# ============================================================
# NEW: PASSWORD RESET AUDIT LOG
# ============================================================

class PasswordResetAuditLog(Base):
    """Track all password reset events for security auditing."""
    __tablename__ = "password_reset_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reset_request_id = Column(Integer, ForeignKey("password_reset_requests.id", ondelete="CASCADE"), nullable=True)
    
    event_type = Column(String(50), nullable=False)  # 'request', 'reset_success', 'reset_failed', 'expired', 'revoked'
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Details about the event
    details = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reset_request = relationship("PasswordReset", foreign_keys=[reset_request_id])
    
    def __repr__(self) -> str:
        return f"<PasswordResetAuditLog {self.id} - {self.event_type}>"