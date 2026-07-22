# ============================================================
# AETHER LINK - AUDIT LOG MODEL
# ============================================================
# Purpose: Track all security-sensitive events for compliance
# Security: Immutable logs, all admin actions tracked
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import json

from ..core.database import Base


class AuditEventType(str, enum.Enum):
    """Audit event types."""
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    LOGOUT_ALL = "logout_all"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_RESET_FAILED = "password_reset_failed"
    EMAIL_VERIFIED = "email_verified"
    EMAIL_VERIFICATION_REQUESTED = "email_verification_requested"
    
    # User Management Events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    
    # Course Events
    COURSE_CREATED = "course_created"
    COURSE_UPDATED = "course_updated"
    COURSE_DELETED = "course_deleted"
    COURSE_PUBLISHED = "course_published"
    COURSE_UNPUBLISHED = "course_unpublished"
    
    # Enrollment Events
    ENROLLMENT_CREATED = "enrollment_created"
    ENROLLMENT_ACTIVATED = "enrollment_activated"
    ENROLLMENT_COMPLETED = "enrollment_completed"
    ENROLLMENT_CANCELLED = "enrollment_cancelled"
    
    # Payment Events
    PAYMENT_CREATED = "payment_created"
    PAYMENT_VERIFIED = "payment_verified"
    PAYMENT_REJECTED = "payment_rejected"
    PAYMENT_REFUNDED = "payment_refunded"
    
    # Teacher Events
    TEACHER_INVITED = "teacher_invited"
    TEACHER_INVITATION_ACCEPTED = "teacher_invitation_accepted"
    TEACHER_INVITATION_EXPIRED = "teacher_invitation_expired"
    TEACHER_INVITATION_REVOKED = "teacher_invitation_revoked"
    TEACHER_ASSIGNED = "teacher_assigned"
    TEACHER_UNASSIGNED = "teacher_unassigned"
    
    # Certificate Events
    CERTIFICATE_GENERATED = "certificate_generated"
    CERTIFICATE_REVOKED = "certificate_revoked"
    CERTIFICATE_VERIFIED = "certificate_verified"
    
    # Assignment Events
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_UPDATED = "assignment_updated"
    ASSIGNMENT_DELETED = "assignment_deleted"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    ASSIGNMENT_GRADED = "assignment_graded"
    
    # Forum Events
    FORUM_TOPIC_CREATED = "forum_topic_created"
    FORUM_TOPIC_UPDATED = "forum_topic_updated"
    FORUM_TOPIC_DELETED = "forum_topic_deleted"
    FORUM_REPLY_CREATED = "forum_reply_created"
    FORUM_REPLY_UPDATED = "forum_reply_updated"
    FORUM_REPLY_DELETED = "forum_reply_deleted"
    
    # Software House Events
    CLIENT_CREATED = "client_created"
    CLIENT_UPDATED = "client_updated"
    CLIENT_DELETED = "client_deleted"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    INVOICE_CREATED = "invoice_created"
    INVOICE_PAID = "invoice_paid"
    INVOICE_CANCELLED = "invoice_cancelled"
    
    # AI Hub Events
    AI_AGENT_CREATED = "ai_agent_created"
    AI_AGENT_UPDATED = "ai_agent_updated"
    AI_AGENT_DELETED = "ai_agent_deleted"
    AI_AGENT_SUBSCRIBED = "ai_agent_subscribed"
    AI_AGENT_UNSUBSCRIBED = "ai_agent_unsubscribed"
    AI_API_KEY_CREATED = "ai_api_key_created"
    AI_API_KEY_REVOKED = "ai_api_key_revoked"
    
    # System Events
    SYSTEM_SETTINGS_CHANGED = "system_settings_changed"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_ERROR = "system_error"
    
    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AuditSeverity(str, enum.Enum):
    """Audit severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # Nullable because system events may not have a user
    
    # ============================================================
    # EVENT DATA
    # ============================================================
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default=AuditSeverity.INFO.value, nullable=False, index=True)
    
    # ============================================================
    # DESCRIPTION
    # ============================================================
    description = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    
    # ============================================================
    # REQUEST CONTEXT
    # ============================================================
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Request ID for tracing (from middleware)
    request_id = Column(String(100), nullable=True, index=True)
    
    # HTTP method and path
    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=True)
    
    # ============================================================
    # DETAILS (JSON)
    # ============================================================
    details = Column(JSON, nullable=True)
    # Contains: before/after values, additional context
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # ============================================================
    # RETENTION
    # ============================================================
    retention_days = Column(Integer, default=365, nullable=False)  # Keep logs for 1 year by default
    archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.id} - {self.event_type} - {self.severity}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_critical(self) -> bool:
        """Check if event is critical severity."""
        return self.severity == AuditSeverity.CRITICAL.value
    
    @property
    def is_high(self) -> bool:
        """Check if event is high severity."""
        return self.severity == AuditSeverity.HIGH.value
    
    @property
    def is_info(self) -> bool:
        """Check if event is info severity."""
        return self.severity == AuditSeverity.INFO.value
    
    @property
    def age_days(self) -> float:
        """Get log age in days."""
        if self.created_at is None:
            return 0.0
        delta = func.now() - self.created_at
        return delta.total_seconds() / 86400
    
    @property
    def should_archive(self) -> bool:
        """Check if log should be archived based on retention."""
        return self.age_days > self.retention_days
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def archive(self) -> None:
        """Archive this log entry."""
        self.archived = True
        self.archived_at = func.now()
    
    def add_detail(self, key: str, value: any) -> None:
        """Add a detail to the JSON field."""
        if self.details is None:
            self.details = {}
        self.details[key] = value
    
    def add_before_after(self, before: dict, after: dict) -> None:
        """
        Add before and after values for change events.
        
        Args:
            before: Dictionary of before values
            after: Dictionary of after values
        """
        if self.details is None:
            self.details = {}
        self.details["before"] = before
        self.details["after"] = after
    
    def set_request_context(self, request_id: str, method: str, path: str) -> None:
        """Set request context information."""
        self.request_id = request_id
        self.method = method
        self.path = path
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert audit log to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "message": self.message,
            "ip_address": self.ip_address,
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "age_days": self.age_days,
        }
        
        if include_sensitive:
            data.update({
                "user_agent": self.user_agent,
                "retention_days": self.retention_days,
                "archived": self.archived,
                "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing audit log data (safe for API responses)."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    # ============================================================
    # CLASS METHODS (For creating specific event types)
    # ============================================================
    
    @classmethod
    def create_log(
        cls,
        event_type: str,
        user_id: int = None,
        description: str = None,
        message: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_id: str = None,
        method: str = None,
        path: str = None,
        details: dict = None,
        severity: str = "info",
        retention_days: int = 365
    ) -> "AuditLog":
        """
        Create a new audit log entry.
        
        Args:
            event_type: Type of event (from AuditEventType)
            user_id: ID of the user (if applicable)
            description: Description of the event
            message: Detailed message
            ip_address: IP address of the requester
            user_agent: User agent of the requester
            request_id: Request ID for tracing
            method: HTTP method
            path: HTTP path
            details: Additional details (JSON)
            severity: Severity level (from AuditSeverity)
            retention_days: Days to keep this log
        
        Returns:
            AuditLog instance
        """
        return cls(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            description=description,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            method=method,
            path=path,
            details=details,
            retention_days=retention_days,
        )
    
    @classmethod
    def create_login_success(
        cls,
        user_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a login success audit log."""
        return cls.create_log(
            event_type=AuditEventType.LOGIN_SUCCESS.value,
            user_id=user_id,
            description="User logged in successfully",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.INFO.value,
            details={"login_type": "password"}
        )
    
    @classmethod
    def create_login_failed(
        cls,
        email: str,
        ip_address: str,
        user_agent: str,
        reason: str = "Invalid credentials",
        request_id: str = None
    ) -> "AuditLog":
        """Create a login failed audit log."""
        return cls.create_log(
            event_type=AuditEventType.LOGIN_FAILED.value,
            description=f"Login failed for user: {email}",
            message=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.MEDIUM.value,
            details={"email": email, "reason": reason}
        )
    
    @classmethod
    def create_password_change(
        cls,
        user_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a password change audit log."""
        return cls.create_log(
            event_type=AuditEventType.PASSWORD_CHANGED.value,
            user_id=user_id,
            description="User changed their password",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.HIGH.value,
            details={"change_method": "user_initiated"}
        )
    
    @classmethod
    def create_password_reset_requested(
        cls,
        user_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a password reset request audit log."""
        return cls.create_log(
            event_type=AuditEventType.PASSWORD_RESET_REQUESTED.value,
            user_id=user_id,
            description="User requested password reset",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.MEDIUM.value,
            details={"reset_method": "email"}
        )
    
    @classmethod
    def create_password_reset_completed(
        cls,
        user_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a password reset completion audit log."""
        return cls.create_log(
            event_type=AuditEventType.PASSWORD_RESET_COMPLETED.value,
            user_id=user_id,
            description="User completed password reset",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.HIGH.value,
            details={"reset_method": "email", "all_sessions_revoked": True}
        )
    
    @classmethod
    def create_payment_verified(
        cls,
        admin_id: int,
        enrollment_id: int,
        payment_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a payment verification audit log."""
        return cls.create_log(
            event_type=AuditEventType.PAYMENT_VERIFIED.value,
            user_id=admin_id,
            description=f"Admin verified payment for enrollment {enrollment_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.MEDIUM.value,
            details={
                "enrollment_id": enrollment_id,
                "payment_id": payment_id,
                "verified_by": admin_id
            }
        )
    
    @classmethod
    def create_teacher_invited(
        cls,
        admin_id: int,
        teacher_email: str,
        course_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a teacher invitation audit log."""
        return cls.create_log(
            event_type=AuditEventType.TEACHER_INVITED.value,
            user_id=admin_id,
            description=f"Admin invited teacher {teacher_email} to course {course_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.MEDIUM.value,
            details={
                "teacher_email": teacher_email,
                "course_id": course_id,
                "invited_by": admin_id
            }
        )
    
    @classmethod
    def create_certificate_generated(
        cls,
        student_id: int,
        certificate_id: int,
        enrollment_id: int,
        ip_address: str,
        user_agent: str,
        request_id: str = None
    ) -> "AuditLog":
        """Create a certificate generation audit log."""
        return cls.create_log(
            event_type=AuditEventType.CERTIFICATE_GENERATED.value,
            user_id=student_id,
            description=f"Certificate generated for student {student_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.MEDIUM.value,
            details={
                "certificate_id": certificate_id,
                "enrollment_id": enrollment_id,
                "student_id": student_id
            }
        )
    
    @classmethod
    def create_suspicious_activity(
        cls,
        user_id: int = None,
        message: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: dict = None,
        request_id: str = None
    ) -> "AuditLog":
        """Create a suspicious activity audit log."""
        return cls.create_log(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY.value,
            user_id=user_id,
            description="Suspicious activity detected",
            message=message,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=AuditSeverity.HIGH.value,
            details=details
        )
    
    @classmethod
    def create_unauthorized_access(
        cls,
        user_id: int = None,
        path: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: dict = None,
        request_id: str = None
    ) -> "AuditLog":
        """Create an unauthorized access audit log."""
        return cls.create_log(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS.value,
            user_id=user_id,
            description=f"Unauthorized access attempt to {path}",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            path=path,
            severity=AuditSeverity.CRITICAL.value,
            details=details
        )


# ============================================================
# NEW: AUDIT LOG RETENTION POLICY
# ============================================================

class AuditRetentionPolicy(Base):
    """Configure audit log retention settings."""
    __tablename__ = "audit_retention_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Severity level this policy applies to
    severity = Column(String(20), nullable=False, unique=True, index=True)
    
    # Retention days for this severity
    retention_days = Column(Integer, nullable=False)
    
    # Whether to auto-archive
    auto_archive = Column(Boolean, default=True, nullable=False)
    
    # Whether to auto-delete after retention
    auto_delete = Column(Boolean, default=False, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Admin who last updated
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    def __repr__(self) -> str:
        return f"<AuditRetentionPolicy {self.severity}: {self.retention_days} days>"


# ============================================================
# INITIAL RETENTION POLICIES (To be inserted via migration)
# ============================================================

# INSERT INTO audit_retention_policies (severity, retention_days, auto_archive, auto_delete) VALUES
# ('info', 30, TRUE, TRUE),
# ('low', 90, TRUE, TRUE),
# ('medium', 180, TRUE, FALSE),
# ('high', 365, TRUE, FALSE),
# ('critical', 730, TRUE, FALSE);