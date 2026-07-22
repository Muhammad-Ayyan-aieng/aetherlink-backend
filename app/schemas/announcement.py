# ============================================================
# AETHER LINK - ANNOUNCEMENT SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# ANNOUNCEMENT ENUMS
# ============================================================

class AnnouncementPriorityEnum(str, Enum):
    """Announcement priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AnnouncementStatusEnum(str, Enum):
    """Announcement status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class AnnouncementTargetTypeEnum(str, Enum):
    """Announcement target type enumeration."""
    ALL_USERS = "all_users"
    STUDENTS = "students"
    TEACHERS = "teachers"
    ADMINS = "admins"
    COURSE_SPECIFIC = "course_specific"
    ROLE_SPECIFIC = "role_specific"


# ============================================================
# BASE SCHEMA
# ============================================================

class AnnouncementBase(BaseModel):
    """Base announcement schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# ANNOUNCEMENT CREATE SCHEMA
# ============================================================

class AnnouncementCreate(AnnouncementBase):
    """Schema for creating an announcement."""
    
    title: str = Field(..., min_length=3, max_length=255, description="Announcement title")
    content: str = Field(..., min_length=10, description="Announcement content")
    short_content: Optional[str] = Field(default=None, max_length=200, description="Short content for preview")
    
    priority: AnnouncementPriorityEnum = Field(
        default=AnnouncementPriorityEnum.NORMAL,
        description="Announcement priority"
    )
    
    # NEW: Targeting
    target_type: AnnouncementTargetTypeEnum = Field(
        default=AnnouncementTargetTypeEnum.ALL_USERS,
        description="Target type"
    )
    target_roles: Optional[List[str]] = Field(
        default=None,
        description="Target roles (for role_specific)"
    )
    target_courses: Optional[List[int]] = Field(
        default=None,
        description="Target course IDs (for course_specific)"
    )
    target_users: Optional[List[int]] = Field(
        default=None,
        description="Target user IDs (for specific users)"
    )
    course_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Course ID (for course-specific announcements)"
    )
    
    # NEW: Schedule & Expiry
    scheduled_at: Optional[datetime] = Field(
        default=None,
        description="Schedule for future publishing"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiry timestamp"
    )
    
    # NEW: Visual & Styling
    icon: Optional[str] = Field(default=None, max_length=50, description="Font Awesome icon")
    banner_image_url: Optional[str] = Field(default=None, max_length=500, description="Banner image URL")
    bg_color: Optional[str] = Field(default=None, max_length=7, description="Background color (hex)")
    text_color: Optional[str] = Field(default=None, max_length=7, description="Text color (hex)")
    
    @field_validator('scheduled_at')
    @classmethod
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate scheduled_at is in the future."""
        if v and v < datetime.now():
            raise ValueError('Scheduled time must be in the future')
        return v


# ============================================================
# ANNOUNCEMENT UPDATE SCHEMA
# ============================================================

class AnnouncementUpdate(AnnouncementBase):
    """Schema for updating an announcement."""
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Announcement title")
    content: Optional[str] = Field(default=None, min_length=10, description="Announcement content")
    short_content: Optional[str] = Field(default=None, max_length=200, description="Short content")
    
    priority: Optional[AnnouncementPriorityEnum] = Field(default=None, description="Announcement priority")
    status: Optional[AnnouncementStatusEnum] = Field(default=None, description="Announcement status")
    
    # NEW: Targeting updates
    target_type: Optional[AnnouncementTargetTypeEnum] = Field(default=None, description="Target type")
    target_roles: Optional[List[str]] = Field(default=None, description="Target roles")
    target_courses: Optional[List[int]] = Field(default=None, description="Target course IDs")
    target_users: Optional[List[int]] = Field(default=None, description="Target user IDs")
    course_id: Optional[int] = Field(default=None, gt=0, description="Course ID")
    
    # NEW: Schedule & Expiry
    scheduled_at: Optional[datetime] = Field(default=None, description="Schedule for future publishing")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    
    # NEW: Visual & Styling
    icon: Optional[str] = Field(default=None, max_length=50, description="Font Awesome icon")
    banner_image_url: Optional[str] = Field(default=None, max_length=500, description="Banner image URL")
    bg_color: Optional[str] = Field(default=None, max_length=7, description="Background color (hex)")
    text_color: Optional[str] = Field(default=None, max_length=7, description="Text color (hex)")


# ============================================================
# ANNOUNCEMENT PUBLISH SCHEMA
# ============================================================

class AnnouncementPublish(AnnouncementBase):
    """Schema for publishing an announcement."""
    
    publish: bool = Field(..., description="True to publish, False to unpublish")
    notify_users: bool = Field(default=True, description="Send notifications to target users")


# ============================================================
# ANNOUNCEMENT RESPONSE SCHEMA
# ============================================================

class AnnouncementResponse(AnnouncementBase):
    """Schema for announcement response."""
    
    id: int = Field(..., description="Announcement ID")
    title: str = Field(..., description="Announcement title")
    content: str = Field(..., description="Announcement content")
    short_content: Optional[str] = Field(default=None, description="Short content")
    
    priority: str = Field(..., description="Announcement priority")
    display_priority: str = Field(..., description="Human-readable priority")
    
    status: str = Field(..., description="Announcement status")
    display_status: str = Field(..., description="Human-readable status")
    
    # NEW: Targeting
    target_type: str = Field(..., description="Target type")
    display_target: str = Field(..., description="Human-readable target")
    is_for_all_users: bool = Field(..., description="Is for all users")
    is_urgent: bool = Field(..., description="Is urgent priority")
    
    course_id: Optional[int] = Field(default=None, description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    days_until_expiry: int = Field(..., description="Days until expiry")
    is_expired: bool = Field(..., description="Is expired")
    
    # NEW: Schedule
    scheduled_at: Optional[datetime] = Field(default=None, description="Scheduled time")
    is_scheduled: bool = Field(..., description="Is scheduled")
    
    # NEW: Visual
    icon: Optional[str] = Field(default=None, description="Icon name")
    banner_image_url: Optional[str] = Field(default=None, description="Banner image URL")
    bg_color: Optional[str] = Field(default=None, description="Background color")
    text_color: Optional[str] = Field(default=None, description="Text color")
    
    # NEW: Statistics
    views_count: int = Field(..., description="View count")
    read_count: int = Field(..., description="Read count")
    click_count: int = Field(..., description="Click count")
    read_rate: float = Field(..., description="Read rate percentage")
    
    created_by: int = Field(..., description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# ANNOUNCEMENT READ RESPONSE
# ============================================================

class AnnouncementReadResponse(AnnouncementBase):
    """Schema for announcement read record."""
    
    id: int = Field(..., description="Read record ID")
    announcement_id: int = Field(..., description="Announcement ID")
    user_id: int = Field(..., description="User ID")
    user_name: Optional[str] = Field(default=None, description="User name")
    read_at: datetime = Field(..., description="Read timestamp")
    read_duration_seconds: Optional[int] = Field(default=None, description="Read duration in seconds")
    device_type: Optional[str] = Field(default=None, description="Device type")
    notification_method: Optional[str] = Field(default=None, description="Notification method")


# ============================================================
# ANNOUNCEMENT DETAIL RESPONSE
# ============================================================

class AnnouncementDetailResponse(AnnouncementResponse):
    """Schema for announcement detail response with read tracking."""
    
    # NEW: Read tracking
    reads: Optional[List[AnnouncementReadResponse]] = Field(
        default=None,
        description="Read records"
    )
    total_reads: int = Field(default=0, description="Total reads")
    unique_readers: int = Field(default=0, description="Unique readers")
    
    # NEW: User-specific
    user_has_read: bool = Field(default=False, description="Current user has read")
    user_read_at: Optional[datetime] = Field(default=None, description="Current user read at")


# ============================================================
# ANNOUNCEMENT LIST REQUEST (Filters)
# ============================================================

class AnnouncementListRequest(AnnouncementBase):
    """Schema for announcement list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title or content")
    status: Optional[AnnouncementStatusEnum] = Field(default=None, description="Filter by status")
    priority: Optional[AnnouncementPriorityEnum] = Field(default=None, description="Filter by priority")
    target_type: Optional[AnnouncementTargetTypeEnum] = Field(default=None, description="Filter by target type")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    created_by: Optional[int] = Field(default=None, description="Filter by creator")
    is_expired: Optional[bool] = Field(default=None, description="Filter by expired")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# ANNOUNCEMENT LIST RESPONSE
# ============================================================

class AnnouncementListResponse(AnnouncementBase):
    """Schema for paginated announcement list response."""
    
    announcements: List[AnnouncementResponse] = Field(..., description="List of announcements")
    total: int = Field(..., description="Total announcements")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# ANNOUNCEMENT STATISTICS (Admin View)
# ============================================================

class AnnouncementStatistics(AnnouncementBase):
    """Schema for announcement statistics."""
    
    total_announcements: int = Field(..., description="Total announcements")
    draft: int = Field(..., description="Draft announcements")
    published: int = Field(..., description="Published announcements")
    archived: int = Field(..., description="Archived announcements")
    expired: int = Field(..., description="Expired announcements")
    
    # NEW: Priority breakdown
    low_priority: int = Field(..., description="Low priority")
    normal_priority: int = Field(..., description="Normal priority")
    high_priority: int = Field(..., description="High priority")
    urgent_priority: int = Field(..., description="Urgent priority")
    
    # NEW: Target breakdown
    target_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Announcements by target type"
    )
    
    # NEW: Engagement stats
    total_views: int = Field(..., description="Total views")
    total_reads: int = Field(..., description="Total reads")
    average_read_rate: float = Field(..., description="Average read rate")
    
    # NEW: Most read announcements
    most_read: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most read announcements"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily announcement trends"
    )


# ============================================================
# ANNOUNCEMENT TEMPLATE SCHEMAS
# ============================================================

class AnnouncementTemplateCreate(AnnouncementBase):
    """Schema for creating an announcement template."""
    
    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    title_template: str = Field(..., min_length=3, max_length=255, description="Title template")
    content_template: str = Field(..., min_length=10, description="Content template")
    short_content_template: Optional[str] = Field(default=None, max_length=200, description="Short content template")
    
    default_priority: AnnouncementPriorityEnum = Field(
        default=AnnouncementPriorityEnum.NORMAL,
        description="Default priority"
    )
    default_target_type: AnnouncementTargetTypeEnum = Field(
        default=AnnouncementTargetTypeEnum.ALL_USERS,
        description="Default target type"
    )
    default_icon: Optional[str] = Field(default=None, max_length=50, description="Default icon")
    default_bg_color: Optional[str] = Field(default=None, max_length=7, description="Default background color")
    default_text_color: Optional[str] = Field(default=None, max_length=7, description="Default text color")
    
    placeholders: Optional[List[str]] = Field(
        default=None,
        description="Placeholders used in templates"
    )
    is_system: bool = Field(default=False, description="System template (can't be deleted)")


class AnnouncementTemplateUpdate(AnnouncementBase):
    """Schema for updating an announcement template."""
    
    name: Optional[str] = Field(default=None, min_length=3, max_length=100, description="Template name")
    title_template: Optional[str] = Field(default=None, max_length=255, description="Title template")
    content_template: Optional[str] = Field(default=None, min_length=10, description="Content template")
    short_content_template: Optional[str] = Field(default=None, max_length=200, description="Short content template")
    
    default_priority: Optional[AnnouncementPriorityEnum] = Field(default=None, description="Default priority")
    default_target_type: Optional[AnnouncementTargetTypeEnum] = Field(default=None, description="Default target type")
    default_icon: Optional[str] = Field(default=None, max_length=50, description="Default icon")
    default_bg_color: Optional[str] = Field(default=None, max_length=7, description="Default background color")
    default_text_color: Optional[str] = Field(default=None, max_length=7, description="Default text color")
    
    placeholders: Optional[List[str]] = Field(default=None, description="Placeholders")
    is_active: Optional[bool] = Field(default=None, description="Is template active")


class AnnouncementTemplateResponse(AnnouncementBase):
    """Schema for announcement template response."""
    
    id: int = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    title_template: str = Field(..., description="Title template")
    content_template: str = Field(..., description="Content template")
    short_content_template: Optional[str] = Field(default=None, description="Short content template")
    
    default_priority: str = Field(..., description="Default priority")
    default_target_type: str = Field(..., description="Default target type")
    default_icon: Optional[str] = Field(default=None, description="Default icon")
    default_bg_color: Optional[str] = Field(default=None, description="Default background color")
    default_text_color: Optional[str] = Field(default=None, description="Default text color")
    
    placeholders: Optional[List[str]] = Field(default=None, description="Placeholders")
    is_active: bool = Field(..., description="Is active")
    is_system: bool = Field(..., description="Is system template")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# BULK ANNOUNCEMENT SCHEMA
# ============================================================

class BulkAnnouncementCreate(AnnouncementBase):
    """Schema for bulk creating announcements (for multiple courses)."""
    
    title: str = Field(..., min_length=3, max_length=255, description="Announcement title")
    content: str = Field(..., min_length=10, description="Announcement content")
    short_content: Optional[str] = Field(default=None, max_length=200, description="Short content")
    
    priority: AnnouncementPriorityEnum = Field(
        default=AnnouncementPriorityEnum.NORMAL,
        description="Announcement priority"
    )
    
    course_ids: List[int] = Field(..., min_length=1, description="List of course IDs")
    
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    icon: Optional[str] = Field(default=None, max_length=50, description="Font Awesome icon")
    bg_color: Optional[str] = Field(default=None, max_length=7, description="Background color (hex)")
    text_color: Optional[str] = Field(default=None, max_length=7, description="Text color (hex)")


class BulkAnnouncementResponse(AnnouncementBase):
    """Schema for bulk announcement response."""
    
    success_count: int = Field(..., description="Number of successful announcements")
    failed_count: int = Field(..., description="Number of failed announcements")
    created_announcements: List[AnnouncementResponse] = Field(
        default_factory=list,
        description="Created announcements"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "AnnouncementPriorityEnum",
    "AnnouncementStatusEnum",
    "AnnouncementTargetTypeEnum",
    "AnnouncementCreate",
    "AnnouncementUpdate",
    "AnnouncementPublish",
    "AnnouncementResponse",
    "AnnouncementReadResponse",
    "AnnouncementDetailResponse",
    "AnnouncementListRequest",
    "AnnouncementListResponse",
    "AnnouncementStatistics",
    "AnnouncementTemplateCreate",
    "AnnouncementTemplateUpdate",
    "AnnouncementTemplateResponse",
    "BulkAnnouncementCreate",
    "BulkAnnouncementResponse",
]