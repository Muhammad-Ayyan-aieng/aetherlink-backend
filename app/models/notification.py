# ============================================================
# AETHER LINK - NOTIFICATION MODEL
# ============================================================
# Purpose: Manage all user notifications (in-app and email)
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class NotificationType(str, enum.Enum):
    """Notification type enumeration."""
    # Enrollment notifications
    ENROLLMENT_CREATED = "enrollment_created"
    ENROLLMENT_ACTIVATED = "enrollment_activated"
    ENROLLMENT_COMPLETED = "enrollment_completed"
    ENROLLMENT_CANCELLED = "enrollment_cancelled"
    
    # Payment notifications
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_VERIFIED = "payment_verified"
    PAYMENT_REJECTED = "payment_rejected"
    PAYMENT_REFUNDED = "payment_refunded"
    
    # Attendance notifications
    ATTENDANCE_MISSED = "attendance_missed"
    ATTENDANCE_MADE_UP = "attendance_made_up"
    ATTENDANCE_REMINDER = "attendance_reminder"
    
    # Course notifications
    COURSE_PUBLISHED = "course_published"
    COURSE_UPDATED = "course_updated"
    COURSE_REMOVED = "course_removed"
    
    # Session notifications
    SESSION_UPCOMING = "session_upcoming"
    SESSION_REMINDER = "session_reminder"
    SESSION_CANCELLED = "session_cancelled"
    SESSION_RECORDING_AVAILABLE = "session_recording_available"
    
    # Teacher notifications
    TEACHER_INVITATION = "teacher_invitation"
    TEACHER_ACCEPTED = "teacher_accepted"
    TEACHER_ASSIGNED = "teacher_assigned"
    
    # Certificate notifications
    CERTIFICATE_ISSUED = "certificate_issued"
    CERTIFICATE_REVOKED = "certificate_revoked"
    
    # Assignment notifications
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_DUE = "assignment_due"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    ASSIGNMENT_GRADED = "assignment_graded"
    
    # Forum notifications
    FORUM_TOPIC_CREATED = "forum_topic_created"
    FORUM_REPLY_CREATED = "forum_reply_created"
    FORUM_REPLY_LIKED = "forum_reply_liked"
    
    # Announcement notifications
    ANNOUNCEMENT_PUBLISHED = "announcement_published"
    
    # System notifications
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"
    ACCOUNT_ACTIVATED = "account_activated"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    PASSWORD_CHANGED = "password_changed"
    
    # Software House notifications
    CLIENT_CREATED = "client_created"
    PROJECT_ASSIGNED = "project_assigned"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    INVOICE_GENERATED = "invoice_generated"
    INVOICE_PAID = "invoice_paid"
    
    # AI Hub notifications
    AI_AGENT_DEPLOYED = "ai_agent_deployed"
    AI_AGENT_SUBSCRIBED = "ai_agent_subscribed"
    AI_API_KEY_CREATED = "ai_api_key_created"
    
    # General
    WELCOME = "welcome"
    REMINDER = "reminder"
    ALERT = "alert"
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"


class NotificationPriority(str, enum.Enum):
    """Notification priority level."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channel."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    ALL = "all"


class NotificationStatus(str, enum.Enum):
    """Notification status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Notification(Base):
    __tablename__ = "notifications"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # NOTIFICATION DETAILS
    # ============================================================
    type = Column(
        String(50),
        nullable=False,
        index=True
    )
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    short_message = Column(String(100), nullable=True)  # For push notifications
    
    # ============================================================
    # ACTION & LINK
    # ============================================================
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    action_data = Column(JSON, nullable=True)  # Additional action data
    
    # ============================================================
    # ICON & IMAGE
    # ============================================================
    icon = Column(String(50), nullable=True)  # Font Awesome icon name
    image_url = Column(String(500), nullable=True)
    
    # ============================================================
    # PRIORITY & CHANNELS
    # ============================================================
    priority = Column(
        String(20),
        default=NotificationPriority.NORMAL.value,
        nullable=False,
        index=True
    )
    
    channel = Column(
        String(20),
        default=NotificationChannel.ALL.value,
        nullable=False
    )
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=NotificationStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # DELIVERY TRACKING
    # ============================================================
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # ============================================================
    # NEW: RETRY TRACKING
    # ============================================================
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: EXPIRY
    # ============================================================
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_expired = Column(Boolean, default=False, nullable=False, index=True)
    
    # ============================================================
    # NEW: GROUPING
    # ============================================================
    group_id = Column(String(100), nullable=True, index=True)  # Group related notifications
    parent_id = Column(Integer, ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    # Example: {"enrollment_id": 123, "session_id": 456, "course_id": 789}
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_notifications_user_unread', 'user_id', 'is_read'),
        Index('ix_notifications_user_created', 'user_id', 'created_at'),
        Index('ix_notifications_user_priority', 'user_id', 'priority'),
        Index('ix_notifications_user_status', 'user_id', 'status'),
        Index('ix_notifications_type_created', 'type', 'created_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user = relationship(
        "User",
        back_populates="notifications",
        foreign_keys=[user_id]
    )
    
    parent = relationship(
        "Notification",
        remote_side=[id],
        foreign_keys=[parent_id],
        uselist=False
    )
    
    children = relationship(
        "Notification",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Notification {self.id}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_read(self) -> bool:
        """Check if notification is read."""
        return self.status == NotificationStatus.READ.value
    
    @property
    def is_unread(self) -> bool:
        """Check if notification is unread."""
        return self.status != NotificationStatus.READ.value
    
    @property
    def is_pending(self) -> bool:
        """Check if notification is pending delivery."""
        return self.status == NotificationStatus.PENDING.value
    
    @property
    def is_sent(self) -> bool:
        """Check if notification was sent."""
        return self.status == NotificationStatus.SENT.value
    
    @property
    def is_delivered(self) -> bool:
        """Check if notification was delivered."""
        return self.status == NotificationStatus.DELIVERED.value
    
    @property
    def is_failed(self) -> bool:
        """Check if notification failed."""
        return self.status == NotificationStatus.FAILED.value
    
    @property
    def is_expired_notification(self) -> bool:
        """Check if notification has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at <= func.now() or self.is_expired
    
    @property
    def is_urgent(self) -> bool:
        """Check if notification is urgent."""
        return self.priority == NotificationPriority.URGENT.value
    
    @property
    def is_high_priority(self) -> bool:
        """Check if notification has high priority."""
        return self.priority in [NotificationPriority.HIGH.value, NotificationPriority.URGENT.value]
    
    @property
    def age_minutes(self) -> float:
        """Get notification age in minutes."""
        if self.created_at is None:
            return 0.0
        delta = func.now() - self.created_at
        return delta.total_seconds() / 60
    
    @property
    def age_hours(self) -> float:
        """Get notification age in hours."""
        return self.age_minutes / 60
    
    @property
    def age_days(self) -> float:
        """Get notification age in days."""
        return self.age_hours / 24
    
    @property
    def priority_display(self) -> str:
        """Get human-readable priority."""
        priority_map = {
            "low": "Low",
            "normal": "Normal",
            "high": "High",
            "urgent": "Urgent",
        }
        return priority_map.get(self.priority, "Normal")
    
    @property
    def type_display(self) -> str:
        """Get human-readable type."""
        type_map = {
            "enrollment_created": "Enrollment Created",
            "enrollment_activated": "Enrollment Activated",
            "enrollment_completed": "Course Completed",
            "payment_received": "Payment Received",
            "payment_verified": "Payment Verified",
            "payment_rejected": "Payment Rejected",
            "attendance_missed": "Session Missed",
            "attendance_made_up": "Session Made Up",
            "session_upcoming": "Session Upcoming",
            "session_recording_available": "Recording Available",
            "teacher_invitation": "Teaching Invitation",
            "certificate_issued": "Certificate Issued",
            "assignment_created": "Assignment Created",
            "assignment_due": "Assignment Due",
            "assignment_graded": "Assignment Graded",
            "forum_reply_created": "New Reply",
            "announcement_published": "Announcement",
            "welcome": "Welcome",
            "reminder": "Reminder",
            "alert": "Alert",
            "info": "Information",
            "success": "Success",
            "error": "Error",
        }
        return type_map.get(self.type, self.type.replace('_', ' ').title())
    
    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def mark_read(self) -> None:
        """Mark notification as read."""
        self.status = NotificationStatus.READ.value
        self.is_read = True
        self.read_at = func.now()
    
    def mark_unread(self) -> None:
        """Mark notification as unread."""
        self.status = NotificationStatus.SENT.value
        self.is_read = False
        self.read_at = None
    
    def mark_sent(self) -> None:
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT.value
        self.sent_at = func.now()
    
    def mark_delivered(self) -> None:
        """Mark notification as delivered."""
        self.status = NotificationStatus.DELIVERED.value
        self.delivered_at = func.now()
    
    def mark_failed(self, reason: str = None) -> None:
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED.value
        self.failed_at = func.now()
        if reason:
            self.failure_reason = reason
        self.retry_count += 1
        self.last_retry_at = func.now()
    
    def mark_cancelled(self) -> None:
        """Mark notification as cancelled."""
        self.status = NotificationStatus.CANCELLED.value
    
    def set_expiry(self, days: int = 7) -> None:
        """Set notification expiry date."""
        self.expires_at = func.now() + func.interval(f'{days} days')
    
    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.last_retry_at = func.now()
    
    def reset_retries(self) -> None:
        """Reset retry count."""
        self.retry_count = 0
        self.last_retry_at = None
    
    def set_channel(self, channel: str) -> None:
        """Set notification channel."""
        if channel in [c.value for c in NotificationChannel]:
            self.channel = channel
    
    def set_priority(self, priority: str) -> None:
        """Set notification priority."""
        if priority in [p.value for p in NotificationPriority]:
            self.priority = priority
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def add_action(self, url: str, text: str = None, data: dict = None) -> None:
        """Add action to notification."""
        self.action_url = url
        if text:
            self.action_text = text
        if data:
            self.action_data = data
    
    def soft_delete(self) -> None:
        """Soft delete the notification."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted notification."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate title length."""
        return 3 <= len(title) <= 255
    
    @staticmethod
    def validate_message(message: str) -> bool:
        """Validate message length."""
        return 1 <= len(message) <= 5000
    
    @staticmethod
    def validate_short_message(short: str) -> bool:
        """Validate short message length."""
        return short is None or len(short) <= 100
    
    @staticmethod
    def validate_priority(priority: str) -> bool:
        """Validate priority."""
        return priority in [p.value for p in NotificationPriority]
    
    @staticmethod
    def validate_channel(channel: str) -> bool:
        """Validate channel."""
        return channel in [c.value for c in NotificationChannel]
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert notification to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "type_display": self.type_display,
            "title": self.title,
            "message": self.message,
            "short_message": self.short_message,
            "is_read": self.is_read,
            "is_unread": self.is_unread,
            "priority": self.priority,
            "priority_display": self.priority_display,
            "is_urgent": self.is_urgent,
            "is_expired": self.is_expired_notification,
            "age_minutes": self.age_minutes,
            "age_hours": self.age_hours,
            "age_days": self.age_days,
            "action_url": self.action_url,
            "action_text": self.action_text,
            "icon": self.icon,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
        
        if include_sensitive:
            data.update({
                "status": self.status,
                "channel": self.channel,
                "action_data": self.action_data,
                "sent_at": self.sent_at.isoformat() if self.sent_at else None,
                "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
                "failed_at": self.failed_at.isoformat() if self.failed_at else None,
                "failure_reason": self.failure_reason,
                "expires_at": self.expires_at.isoformat() if self.expires_at else None,
                "group_id": self.group_id,
                "parent_id": self.parent_id,
                "retry_count": self.retry_count,
                "can_retry": self.can_retry,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing notification data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("metadata", None)
        data.pop("action_data", None)
        return data
    
    def to_user_json(self) -> dict:
        """User-facing notification data."""
        return self.to_public_json()
    
    def to_admin_json(self) -> dict:
        """Admin-facing notification data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: NOTIFICATION PREFERENCE
# ============================================================

class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Channel preferences (per type)
    channels = Column(JSON, nullable=True)
    # Example: {"email": true, "push": true, "sms": false, "in_app": true}
    
    # Type-specific preferences
    preferences = Column(JSON, nullable=True)
    # Example: {"enrollment_created": {"email": true, "in_app": true}, ...}
    
    # Quiet hours
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # "07:00"
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    
    # Frequency
    digest_enabled = Column(Boolean, default=False, nullable=False)
    digest_frequency = Column(String(20), nullable=True)  # daily, weekly, monthly
    
    # Do Not Disturb
    dnd_enabled = Column(Boolean, default=False, nullable=False)
    dnd_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<NotificationPreference {self.user_id}>"
    
    def is_channel_enabled(self, channel: str) -> bool:
        """Check if a channel is enabled."""
        if self.channels is None:
            return True  # Default: all channels enabled
        return self.channels.get(channel, True)
    
    def is_type_enabled(self, notification_type: str, channel: str) -> bool:
        """Check if a specific notification type is enabled for a channel."""
        if self.preferences is None:
            return True  # Default: all types enabled
        type_prefs = self.preferences.get(notification_type, {})
        return type_prefs.get(channel, True)
    
    def set_channel_preference(self, channel: str, enabled: bool) -> None:
        """Set channel preference."""
        if self.channels is None:
            self.channels = {}
        self.channels[channel] = enabled
    
    def set_type_preference(self, notification_type: str, channel: str, enabled: bool) -> None:
        """Set type-specific channel preference."""
        if self.preferences is None:
            self.preferences = {}
        if notification_type not in self.preferences:
            self.preferences[notification_type] = {}
        self.preferences[notification_type][channel] = enabled
    
    def is_in_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled:
            return False
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False
        
        from datetime import datetime
        now = datetime.now().time()
        start = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(self.quiet_hours_end, "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:  # Wraps around midnight
            return now >= start or now <= end


# ============================================================
# NEW: NOTIFICATION TEMPLATE
# ============================================================

class NotificationTemplate(Base):
    """Pre-defined notification templates."""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    
    # Content
    title_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    short_message_template = Column(String(100), nullable=True)
    
    # Defaults
    default_priority = Column(String(20), default=NotificationPriority.NORMAL.value, nullable=False)
    default_channel = Column(String(20), default=NotificationChannel.ALL.value, nullable=False)
    default_icon = Column(String(50), nullable=True)
    
    # Placeholders (for validation)
    required_placeholders = Column(JSON, nullable=True)
    # Example: ["student_name", "course_name", "session_name"]
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # Can't be deleted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<NotificationTemplate {self.name}>"
    
    def render_title(self, context: dict) -> str:
        """Render title with placeholders."""
        result = self.title_template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    def render_message(self, context: dict) -> str:
        """Render message with placeholders."""
        result = self.message_template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    def render_short_message(self, context: dict) -> str:
        """Render short message with placeholders."""
        if self.short_message_template is None:
            return self.render_message(context)[:100]
        result = self.short_message_template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


# ============================================================
# NEW: NOTIFICATION BATCH (For bulk notifications)
# ============================================================

class NotificationBatch(Base):
    """Batch notification jobs."""
    __tablename__ = "notification_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Batch details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Type
    template_id = Column(Integer, ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True)
    type = Column(String(50), nullable=False)
    
    # Target
    target_roles = Column(JSON, nullable=True)  # ["student", "teacher"]
    target_courses = Column(JSON, nullable=True)  # [1, 2, 3]
    target_users = Column(JSON, nullable=True)  # [1, 2, 3]
    
    # Status
    status = Column(String(20), default="draft", nullable=False, index=True)  # draft, processing, completed, failed, cancelled
    
    # Statistics
    total_count = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    # Scheduled delivery
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Created by
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    template = relationship("NotificationTemplate", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f"<NotificationBatch {self.id}: {self.name}>"
    
    @property
    def is_processing(self) -> bool:
        """Check if batch is processing."""
        return self.status == "processing"
    
    @property
    def is_completed(self) -> bool:
        """Check if batch is completed."""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if batch failed."""
        return self.status == "failed"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_count == 0:
            return 0.0
        return (self.sent_count / self.total_count) * 100
    
    def mark_processing(self) -> None:
        """Mark batch as processing."""
        self.status = "processing"
    
    def mark_completed(self) -> None:
        """Mark batch as completed."""
        self.status = "completed"
        self.completed_at = func.now()
    
    def mark_failed(self) -> None:
        """Mark batch as failed."""
        self.status = "failed"
        self.completed_at = func.now()
    
    def mark_cancelled(self) -> None:
        """Mark batch as cancelled."""
        self.status = "cancelled"
        self.completed_at = func.now()