# ============================================================
# AETHER LINK - REFRESH TOKEN MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..core.database import Base


class TokenStatus(str, enum.Enum):
    """Token status enumeration."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REPLACED = "replaced"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # TOKEN DATA
    # ============================================================
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    # Changed from "token" to "token_hash" for security - we only store hashes
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # ============================================================
    # NEW: REVOCATION & REPLACEMENT (TOKEN ROTATION)
    # ============================================================
    revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # NEW: When revoked
    replaced_by_id = Column(Integer, ForeignKey("refresh_tokens.id"), nullable=True, index=True)
    # For tracking token rotation chain
    
    # ============================================================
    # NEW: TOKEN STATUS (Derived, but stored for queries)
    # ============================================================
    status = Column(String(20), default=TokenStatus.ACTIVE.value, nullable=False, index=True)
    
    # ============================================================
    # NEW: DEVICE & LOCATION INFO (For security tracking)
    # ============================================================
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # NEW: Device fingerprint for security
    device_id = Column(String(255), nullable=True, index=True)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    browser_name = Column(String(50), nullable=True)
    browser_version = Column(String(20), nullable=True)
    os_name = Column(String(50), nullable=True)
    os_version = Column(String(20), nullable=True)
    
    # NEW: Location info (geo-ip)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    
    # ============================================================
    # NEW: SECURITY & METADATA
    # ============================================================
    
    # NEW: Token rotation count (track how many times this token was rotated)
    rotation_count = Column(Integer, default=0, nullable=False)
    
    # NEW: Last used timestamp
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_used_ip = Column(String(100), nullable=True)
    last_used_user_agent = Column(Text, nullable=True)
    
    # NEW: Additional metadata (JSON)
    metadata = Column(JSON, nullable=True)
    # Example: {"session_id": "xxx", "login_attempt_id": "yyy"}
    
    # NEW: Supabase JTI (JWT ID) for cross-referencing
    supabase_jti = Column(String(255), nullable=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # User relationship
    user = relationship(
        "User",
        back_populates="refresh_tokens",
        foreign_keys=[user_id]
    )
    
    # Replacement token relationship
    replaced_by = relationship(
        "RefreshToken",
        remote_side=[id],
        uselist=False,
        foreign_keys=[replaced_by_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<RefreshToken {self.id} for user {self.user_id}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active(self) -> bool:
        """Check if token is currently active."""
        return (
            not self.revoked
            and self.expires_at > func.now()
            and self.status == TokenStatus.ACTIVE.value
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return self.expires_at <= func.now()
    
    @property
    def is_revoked(self) -> bool:
        """Check if token is revoked."""
        return self.revoked
    
    @property
    def is_replaced(self) -> bool:
        """Check if token was replaced by a new one."""
        return self.replaced_by_id is not None
    
    @property
    def age_hours(self) -> float:
        """Get token age in hours."""
        if self.created_at is None:
            return 0.0
        delta = func.now() - self.created_at
        return delta.total_seconds() / 3600
    
    @property
    def device_info(self) -> dict:
        """Get device information as dictionary."""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "browser": {
                "name": self.browser_name,
                "version": self.browser_version,
            },
            "os": {
                "name": self.os_name,
                "version": self.os_version,
            },
        }
    
    @property
    def location_info(self) -> dict:
        """Get location information as dictionary."""
        return {
            "country": self.country,
            "city": self.city,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
        }
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def revoke(self) -> None:
        """Revoke this token."""
        self.revoked = True
        self.revoked_at = func.now()
        self.status = TokenStatus.REVOKED.value
    
    def replace(self, new_token_id: int) -> None:
        """Mark this token as replaced by a new one."""
        self.replaced_by_id = new_token_id
        self.status = TokenStatus.REPLACED.value
    
    def mark_used(self, ip_address: str, user_agent: str) -> None:
        """Record token usage."""
        self.last_used_at = func.now()
        self.last_used_ip = ip_address
        self.last_used_user_agent = user_agent
    
    def increment_rotation(self) -> None:
        """Increment rotation count."""
        self.rotation_count += 1
    
    def set_device_info(self, **kwargs) -> None:
        """Set device information from parsed headers."""
        if "device_id" in kwargs:
            self.device_id = kwargs["device_id"]
        if "device_name" in kwargs:
            self.device_name = kwargs["device_name"]
        if "device_type" in kwargs:
            self.device_type = kwargs["device_type"]
        if "browser_name" in kwargs:
            self.browser_name = kwargs["browser_name"]
        if "browser_version" in kwargs:
            self.browser_version = kwargs["browser_version"]
        if "os_name" in kwargs:
            self.os_name = kwargs["os_name"]
        if "os_version" in kwargs:
            self.os_version = kwargs["os_version"]
    
    def set_location_info(self, **kwargs) -> None:
        """Set location information from geo-ip."""
        if "country" in kwargs:
            self.country = kwargs["country"]
        if "city" in kwargs:
            self.city = kwargs["city"]
        if "latitude" in kwargs:
            self.latitude = kwargs["latitude"]
        if "longitude" in kwargs:
            self.longitude = kwargs["longitude"]
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert token to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "is_active": self.is_active,
            "ip_address": self.ip_address,
            "device_info": self.device_info,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
        
        if include_sensitive:
            data.update({
                "token_hash": self.token_hash,
                "revoked": self.revoked,
                "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
                "replaced_by_id": self.replaced_by_id,
                "rotation_count": self.rotation_count,
                "supabase_jti": self.supabase_jti,
                "location_info": self.location_info,
                "metadata": self.metadata,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing token data (safe for API responses)."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "is_active": self.is_active,
            "device_info": self.device_info,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
    
    # ============================================================
    # CLASS METHODS
    # ============================================================
    
    @classmethod
    def create_from_supabase(
        cls,
        user_id: int,
        supabase_token: str,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None,
        **kwargs
    ) -> "RefreshToken":
        """
        Create a RefreshToken from Supabase auth data.
        
        Args:
            user_id: User ID
            supabase_token: The refresh token from Supabase
            expires_at: Expiry datetime
            ip_address: IP address of the request
            user_agent: User agent of the request
            **kwargs: Additional fields (device_id, device_name, etc.)
        """
        # Store only the hash of the token for security
        import hashlib
        token_hash = hashlib.sha256(supabase_token.encode()).hexdigest()
        
        return cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            status=TokenStatus.ACTIVE.value,
            **kwargs
        )


# ============================================================
# NEW: TOKEN REVOCATION LOG (Audit Trail)
# ============================================================

class TokenRevocationLog(Base):
    """Track all token revocations for security auditing."""
    __tablename__ = "token_revocation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("refresh_tokens.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(100), nullable=False)  # 'logout', 'password_change', 'admin_revoke', 'expired'
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    token = relationship("RefreshToken", foreign_keys=[token_id])
    user = relationship("User", foreign_keys=[user_id])
    revoker = relationship("User", foreign_keys=[revoked_by])
    
    def __repr__(self) -> str:
        return f"<TokenRevocationLog {self.id} - {self.reason}>"