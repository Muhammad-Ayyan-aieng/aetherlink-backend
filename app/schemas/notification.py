# ============================================================
# AETHER LINK - NOTIFICATION SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# NOTIFICATION ENUMS
# ============================================================

class NotificationTypeEnum(str, Enum):
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


class NotificationPriorityEnum(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannelEnum(str, Enum):
    """Notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    ALL = "all"


class NotificationStatusEnum(str, Enum):
    """Notification status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================
# BASE SCHEMA
# ============================================================

class NotificationBase(BaseModel):
    """Base notification schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# NOTIFICATION CREATE SCHEMA
# ============================================================

class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    
    user_id: int = Field(..., gt=0, description="User ID")
    type: NotificationTypeEnum = Field(..., description="Notification type")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    short_message: Optional[str] = Field(default=None, max_length=100, description="Short message for push")
    
    # NEW: Action
    action_url: Optional[str] = Field(default=None, max_length=500, description="Action URL")
    action_text: Optional[str] = Field(default=None, max_length=100, description="Action button text")
    action_data: Optional[Dict[str, Any]] = Field(default=None, description="Action data")
    
    # NEW: Icon & Image
    icon: Optional[str] = Field(default=None, max_length=50, description="Icon name")
    image_url: Optional[str] = Field(default=None, max_length=500, description="Image URL")
    
    # NEW: Priority & Channel
    priority: NotificationPriorityEnum = Field(default=NotificationPriorityEnum.NORMAL, description="Priority")
    channel: NotificationChannelEnum = Field(default=NotificationChannelEnum.ALL, description="Delivery channel")
    
    # NEW: Expiry
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    
    # NEW: Grouping
    group_id: Optional[str] = Field(default=None, max_length=100, description="Group ID")
    parent_id: Optional[int] = Field(default=None, description="Parent notification ID")
    
    # NEW: Metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


# ============================================================
# NOTIFICATION UPDATE SCHEMA
# ============================================================

class NotificationUpdate(NotificationBase):
    """Schema for updating a notification."""
    
    status: Optional[NotificationStatusEnum] = Field(default=None, description="Notification status")
    is_read: Optional[bool] = Field(default=None, description="Mark as read")
    
    # NEW: Delivery tracking
    mark_sent: Optional[bool] = Field(default=None, description="Mark as sent")
    mark_delivered: Optional[bool] = Field(default=None, description="Mark as delivered")
    mark_failed: Optional[bool] = Field(default=None, description="Mark as failed")
    failure_reason: Optional[str] = Field(default=None, max_length=500, description="Failure reason")


# ============================================================
# BULK NOTIFICATION CREATE SCHEMA
# ============================================================

class BulkNotificationCreate(NotificationBase):
    """Schema for creating bulk notifications."""
    
    user_ids: List[int] = Field(..., min_length=1, description="List of user IDs")
    type: NotificationTypeEnum = Field(..., description="Notification type")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    short_message: Optional[str] = Field(default=None, max_length=100, description="Short message")
    
    action_url: Optional[str] = Field(default=None, max_length=500, description="Action URL")
    action_text: Optional[str] = Field(default=None, max_length=100, description="Action text")
    icon: Optional[str] = Field(default=None, max_length=50, description="Icon name")
    
    priority: NotificationPriorityEnum = Field(default=NotificationPriorityEnum.NORMAL, description="Priority")
    channel: NotificationChannelEnum = Field(default=NotificationChannelEnum.ALL, description="Delivery channel")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class BulkNotificationResponse(NotificationBase):
    """Schema for bulk notification response."""
    
    success_count: int = Field(..., description="Number of successful notifications")
    failed_count: int = Field(..., description="Number of failed notifications")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")


# ============================================================
# NOTIFICATION RESPONSE SCHEMA
# ============================================================

class NotificationResponse(NotificationBase):
    """Schema for notification response."""
    
    id: int = Field(..., description="Notification ID")
    user_id: int = Field(..., description="User ID")
    type: str = Field(..., description="Notification type")
    type_display: str = Field(..., description="Human-readable type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    short_message: Optional[str] = Field(default=None, description="Short message")
    
    is_read: bool = Field(default=False, description="Is read")
    is_unread: bool = Field(default=True, description="Is unread")
    
    priority: str = Field(default="normal", description="Priority")
    priority_display: str = Field(default="Normal", description="Human-readable priority")
    is_urgent: bool = Field(default=False, description="Is urgent")
    
    is_expired: bool = Field(default=False, description="Is expired")
    age_minutes: float = Field(default=0.0, description="Age in minutes")
    age_hours: float = Field(default=0.0, description="Age in hours")
    age_days: float = Field(default=0.0, description="Age in days")
    
    action_url: Optional[str] = Field(default=None, description="Action URL")
    action_text: Optional[str] = Field(default=None, description="Action text")
    icon: Optional[str] = Field(default=None, description="Icon name")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    
    # NEW: Grouping
    group_id: Optional[str] = Field(default=None, description="Group ID")
    parent_id: Optional[int] = Field(default=None, description="Parent notification ID")
    has_children: bool = Field(default=False, description="Has child notifications")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: Optional[datetime] = Field(default=None, description="Read timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# NOTIFICATION LIST REQUEST (Filters)
# ============================================================

class NotificationListRequest(NotificationBase):
    """Schema for notification list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    is_read: Optional[bool] = Field(default=None, description="Filter by read status")
    type: Optional[NotificationTypeEnum] = Field(default=None, description="Filter by type")
    priority: Optional[NotificationPriorityEnum] = Field(default=None, description="Filter by priority")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# NOTIFICATION LIST RESPONSE
# ============================================================

class NotificationListResponse(NotificationBase):
    """Schema for paginated notification list response."""
    
    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total notifications")
    unread_count: int = Field(..., description="Unread count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# NOTIFICATION PREFERENCE SCHEMAS
# ============================================================

class NotificationPreferenceUpdate(NotificationBase):
    """Schema for updating notification preferences."""
    
    # Channel preferences
    channels: Optional[Dict[str, bool]] = Field(default=None, description="Channel preferences")
    # Example: {"email": true, "push": true, "sms": false, "in_app": true}
    
    # Type-specific preferences
    preferences: Optional[Dict[str, Dict[str, bool]]] = Field(
        default=None,
        description="Type-specific preferences"
    )
    # Example: {"enrollment_created": {"email": true, "in_app": true}}
    
    # Quiet hours
    quiet_hours_start: Optional[str] = Field(default=None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', description="Start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(default=None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', description="End time (HH:MM)")
    quiet_hours_enabled: Optional[bool] = Field(default=None, description="Enable quiet hours")
    
    # Digest
    digest_enabled: Optional[bool] = Field(default=None, description="Enable digest")
    digest_frequency: Optional[str] = Field(default=None, description="Digest frequency (daily, weekly, monthly)")
    
    # Do Not Disturb
    dnd_enabled: Optional[bool] = Field(default=None, description="Enable DND")
    dnd_until: Optional[datetime] = Field(default=None, description="DND until")


class NotificationPreferenceResponse(NotificationBase):
    """Schema for notification preference response."""
    
    user_id: int = Field(..., description="User ID")
    channels: Dict[str, bool] = Field(default_factory=dict, description="Channel preferences")
    preferences: Dict[str, Dict[str, bool]] = Field(default_factory=dict, description="Type preferences")
    quiet_hours_start: Optional[str] = Field(default=None, description="Start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(default=None, description="End time (HH:MM)")
    quiet_hours_enabled: bool = Field(default=False, description="Quiet hours enabled")
    digest_enabled: bool = Field(default=False, description="Digest enabled")
    digest_frequency: Optional[str] = Field(default=None, description="Digest frequency")
    dnd_enabled: bool = Field(default=False, description="DND enabled")
    dnd_until: Optional[datetime] = Field(default=None, description="DND until")


# ============================================================
# NOTIFICATION STATISTICS
# ============================================================

class NotificationStatistics(NotificationBase):
    """Schema for notification statistics."""
    
    total_sent: int = Field(..., description="Total notifications sent")
    total_read: int = Field(..., description="Total read notifications")
    total_unread: int = Field(..., description="Total unread notifications")
    read_rate: float = Field(..., description="Read rate percentage")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Notifications by type"
    )
    
    # NEW: By priority
    priority_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Notifications by priority"
    )
    
    # NEW: Recent trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily notification trends"
    )


# ============================================================
# NOTIFICATION TEMPLATE SCHEMAS
# ============================================================

class NotificationTemplateCreate(NotificationBase):
    """Schema for creating a notification template."""
    
    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    type: NotificationTypeEnum = Field(..., description="Notification type")
    title_template: str = Field(..., min_length=1, max_length=255, description="Title template")
    message_template: str = Field(..., min_length=1, description="Message template")
    short_message_template: Optional[str] = Field(default=None, max_length=100, description="Short message template")
    
    default_priority: NotificationPriorityEnum = Field(
        default=NotificationPriorityEnum.NORMAL,
        description="Default priority"
    )
    default_channel: NotificationChannelEnum = Field(
        default=NotificationChannelEnum.ALL,
        description="Default channel"
    )
    default_icon: Optional[str] = Field(default=None, max_length=50, description="Default icon")
    
    required_placeholders: Optional[List[str]] = Field(
        default=None,
        description="Required placeholders"
    )
    is_system: bool = Field(default=False, description="System template (can't be deleted)")


class NotificationTemplateUpdate(NotificationBase):
    """Schema for updating a notification template."""
    
    name: Optional[str] = Field(default=None, min_length=3, max_length=100, description="Template name")
    title_template: Optional[str] = Field(default=None, max_length=255, description="Title template")
    message_template: Optional[str] = Field(default=None, description="Message template")
    short_message_template: Optional[str] = Field(default=None, max_length=100, description="Short message template")
    
    default_priority: Optional[NotificationPriorityEnum] = Field(default=None, description="Default priority")
    default_channel: Optional[NotificationChannelEnum] = Field(default=None, description="Default channel")
    default_icon: Optional[str] = Field(default=None, max_length=50, description="Default icon")
    
    required_placeholders: Optional[List[str]] = Field(default=None, description="Required placeholders")
    is_active: Optional[bool] = Field(default=None, description="Is template active")


class NotificationTemplateResponse(NotificationBase):
    """Schema for notification template response."""
    
    id: int = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    type: str = Field(..., description="Notification type")
    title_template: str = Field(..., description="Title template")
    message_template: str = Field(..., description="Message template")
    short_message_template: Optional[str] = Field(default=None, description="Short message template")
    
    default_priority: str = Field(..., description="Default priority")
    default_channel: str = Field(..., description="Default channel")
    default_icon: Optional[str] = Field(default=None, description="Default icon")
    
    required_placeholders: Optional[List[str]] = Field(default=None, description="Required placeholders")
    is_active: bool = Field(..., description="Is active")
    is_system: bool = Field(..., description="Is system template")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# MARK NOTIFICATIONS REQUEST
# ============================================================

class MarkNotificationsReadRequest(NotificationBase):
    """Schema for marking notifications as read."""
    
    notification_ids: Optional[List[int]] = Field(
        default=None,
        description="List of notification IDs (None = mark all)"
    )
    mark_all: bool = Field(default=False, description="Mark all as read")


class MarkNotificationsReadResponse(NotificationBase):
    """Schema for marking notifications read response."""
    
    success: bool = Field(..., description="Operation success")
    count: int = Field(..., description="Number of notifications marked as read")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "NotificationTypeEnum",
    "NotificationPriorityEnum",
    "NotificationChannelEnum",
    "NotificationStatusEnum",
    "NotificationCreate",
    "NotificationUpdate",
    "BulkNotificationCreate",
    "BulkNotificationResponse",
    "NotificationResponse",
    "NotificationListRequest",
    "NotificationListResponse",
    "NotificationPreferenceUpdate",
    "NotificationPreferenceResponse",
    "NotificationStatistics",
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "MarkNotificationsReadRequest",
    "MarkNotificationsReadResponse",
]