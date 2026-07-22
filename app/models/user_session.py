# ============================================================
# AETHER LINK - USER SESSION MODEL
# ============================================================
# Purpose: Track active user sessions for "Logout All Devices" feature
# Security: Session tokens are hashed, all devices tracked
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import hashlib

from ..core.database import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class UserSession(Base):
    __tablename__ = "user_sessions"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # SESSION TOKEN (Hashed for security)
    # ============================================================
    session_token_hash = Column(String(128), nullable=False, unique=True, index=True)
    # We only store the hash, never the actual token
    
    # ============================================================
    # DEVICE & LOCATION INFO
    # ============================================================
    # Device identification
    device_id = Column(String(255), nullable=True, index=True)  # Fingerprint
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    browser_name = Column(String(50), nullable=True)
    browser_version = Column(String(20), nullable=True)
    os_name = Column(String(50), nullable=True)
    os_version = Column(String(20), nullable=True)
    
    # Location info (geo-ip)
    ip_address = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    
    # User agent (full string for debugging)
    user_agent = Column(Text, nullable=True)
    
    # ============================================================
    # STATUS & TIMESTAMPS
    # ============================================================
    status = Column(String(20), default=SessionStatus.ACTIVE.value, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Revocation tracking
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(String(100), nullable=True)  # 'logout', 'password_change', 'admin_revoke', 'expired'
    
    # ============================================================
    # SECURITY METRICS
    # ============================================================
    # Track session age and activity
    activity_count = Column(Integer, default=0, nullable=False)  # Number of requests made
    total_session_duration_seconds = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    # Example: {"login_attempt_id": "xxx", "referrer": "https://..."}
    
    # ============================================================
    # SUPABASE INTEGRATION
    # ============================================================
    supabase_session_id = Column(String(255), nullable=True, index=True)  # Supabase session ID
    supabase_refresh_token_jti = Column(String(255), nullable=True, index=True)  # JWT ID
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    user = relationship(
        "User",
        back_populates="user_sessions",
        foreign_keys=[user_id]
    )
    
    revoker = relationship(
        "User",
        foreign_keys=[revoked_by],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<UserSession {self.id} - User {self.user_id} - {self.status}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return (
            self.status == SessionStatus.ACTIVE.value
            and self.expires_at > func.now()
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return self.expires_at <= func.now()
    
    @property
    def is_revoked(self) -> bool:
        """Check if session was revoked."""
        return self.status == SessionStatus.REVOKED.value
    
    @property
    def age_minutes(self) -> float:
        """Get session age in minutes."""
        if self.created_at is None:
            return 0.0
        delta = func.now() - self.created_at
        return delta.total_seconds() / 60
    
    @property
    def age_hours(self) -> float:
        """Get session age in hours."""
        return self.age_minutes / 60
    
    @property
    def idle_minutes(self) -> float:
        """Get idle time in minutes since last activity."""
        if self.last_activity is None:
            return 0.0
        delta = func.now() - self.last_activity
        return delta.total_seconds() / 60
    
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
            "ip": self.ip_address,
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
    
    def revoke(self, reason: str = "logout", revoker_id: int = None) -> None:
        """
        Revoke this session.
        
        Args:
            reason: Reason for revocation (logout, password_change, admin_revoke, expired)
            revoker_id: ID of user who revoked (admin) or None if self-revoked
        """
        self.status = SessionStatus.REVOKED.value
        self.revoked_at = func.now()
        self.revocation_reason = reason
        
        if revoker_id:
            self.revoked_by = revoker_id
    
    def update_activity(self) -> None:
        """Update last activity timestamp and increment activity count."""
        self.last_activity = func.now()
        self.activity_count += 1
    
    def extend_session(self, additional_hours: int = 24) -> None:
        """
        Extend session expiration.
        
        Args:
            additional_hours: Hours to extend (default: 24)
        """
        if self.is_active:
            self.expires_at = self.expires_at + func.interval(f'{additional_hours} hours')
    
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
        if "ip_address" in kwargs:
            self.ip_address = kwargs["ip_address"]
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
    
    def update_duration(self) -> None:
        """Update total session duration."""
        if self.created_at:
            delta = func.now() - self.created_at
            self.total_session_duration_seconds = int(delta.total_seconds())
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert session to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "device_info": self.device_info,
            "location_info": self.location_info,
            "status": self.status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "age_minutes": self.age_minutes,
            "idle_minutes": self.idle_minutes,
            "activity_count": self.activity_count,
        }
        
        if include_sensitive:
            data.update({
                "session_token_hash": self.session_token_hash,
                "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
                "revoked_by": self.revoked_by,
                "revocation_reason": self.revocation_reason,
                "supabase_session_id": self.supabase_session_id,
                "supabase_refresh_token_jti": self.supabase_refresh_token_jti,
                "metadata": self.metadata,
                "total_session_duration_seconds": self.total_session_duration_seconds,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing session data (safe for API responses)."""
        return {
            "id": self.id,
            "device_info": self.device_info,
            "location": {
                "country": self.country,
                "city": self.city,
            },
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "idle_minutes": self.idle_minutes,
        }
    
    # ============================================================
    # CLASS METHODS
    # ============================================================
    
    @classmethod
    def create_from_supabase(
        cls,
        user_id: int,
        session_token: str,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None,
        supabase_session_id: str = None,
        supabase_refresh_token_jti: str = None,
        **kwargs
    ) -> "UserSession":
        """
        Create a UserSession from Supabase auth data.
        
        Args:
            user_id: User ID
            session_token: The session token from Supabase
            expires_at: Expiry datetime
            ip_address: IP address of the request
            user_agent: User agent of the request
            supabase_session_id: Supabase session ID
            supabase_refresh_token_jti: JWT ID of refresh token
            **kwargs: Additional fields (device_id, device_name, etc.)
        """
        # Store only the hash of the token for security
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        return cls(
            user_id=user_id,
            session_token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            supabase_session_id=supabase_session_id,
            supabase_refresh_token_jti=supabase_refresh_token_jti,
            status=SessionStatus.ACTIVE.value,
            **kwargs
        )
    
    @classmethod
    def create_custom(
        cls,
        user_id: int,
        session_token: str,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None,
        **kwargs
    ) -> "UserSession":
        """
        Create a custom UserSession (for custom auth).
        
        Args:
            user_id: User ID
            session_token: The session token
            expires_at: Expiry datetime
            ip_address: IP address of the request
            user_agent: User agent of the request
            **kwargs: Additional fields (device_id, device_name, etc.)
        """
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        return cls(
            user_id=user_id,
            session_token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            status=SessionStatus.ACTIVE.value,
            **kwargs
        )


# ============================================================
# NEW: SESSION REVOCATION LOG (Audit Trail)
# ============================================================

class SessionRevocationLog(Base):
    """Track all session revocations for security auditing."""
    __tablename__ = "session_revocation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(100), nullable=False)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("UserSession", foreign_keys=[session_id])
    user = relationship("User", foreign_keys=[user_id])
    revoker = relationship("User", foreign_keys=[revoked_by])
    
    def __repr__(self) -> str:
        return f"<SessionRevocationLog {self.id} - {self.reason}>"