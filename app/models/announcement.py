# ============================================================
# AETHER LINK - ANNOUNCEMENT MODEL
# ============================================================
# Purpose: System-wide and course-specific announcements
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class AnnouncementPriority(str, enum.Enum):
    """Announcement priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AnnouncementStatus(str, enum.Enum):
    """Announcement status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class AnnouncementTargetType(str, enum.Enum):
    """Announcement target type enumeration."""
    ALL_USERS = "all_users"
    STUDENTS = "students"
    TEACHERS = "teachers"
    ADMINS = "admins"
    COURSE_SPECIFIC = "course_specific"
    ROLE_SPECIFIC = "role_specific"


class Announcement(Base):
    __tablename__ = "announcements"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # NEW: Short content (for preview)
    short_content = Column(String(200), nullable=True)
    
    # ============================================================
    # PRIORITY & STATUS
    # ============================================================
    priority = Column(
        String(20),
        default=AnnouncementPriority.NORMAL.value,
        nullable=False,
        index=True
    )
    
    status = Column(
        String(20),
        default=AnnouncementStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # TARGETING ⭐
    # ============================================================
    target_type = Column(
        String(50),
        default=AnnouncementTargetType.ALL_USERS.value,
        nullable=False
    )
    
    # NEW: Target roles (JSON array)
    target_roles = Column(JSON, nullable=True)
    # Example: ["student", "teacher"]
    
    # NEW: Target courses (JSON array)
    target_courses = Column(JSON, nullable=True)
    # Example: [1, 2, 3]
    
    # NEW: Target users (JSON array - specific users)
    target_users = Column(JSON, nullable=True)
    # Example: [1, 2, 3]
    
    # NEW: Target course IDs (for course-specific announcements)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # ============================================================
    # PUBLISHING & EXPIRY
    # ============================================================
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # NEW: Schedule for future publishing
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # VISUAL & STYLING
    # ============================================================
    # NEW: Icon (Font Awesome)
    icon = Column(String(50), nullable=True)
    
    # NEW: Banner image
    banner_image_url = Column(String(500), nullable=True)
    
    # NEW: Background color
    bg_color = Column(String(7), nullable=True)  # Hex color
    
    # NEW: Text color
    text_color = Column(String(7), nullable=True)  # Hex color
    
    # ============================================================
    # STATISTICS
    # ============================================================
    views_count = Column(Integer, default=0, nullable=False)
    read_count = Column(Integer, default=0, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # CREATOR
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_announcements_status_priority', 'status', 'priority'),
        Index('ix_announcements_published_at', 'published_at'),
        Index('ix_announcements_expires_at', 'expires_at'),
        Index('ix_announcements_created_at', 'created_at'),
        Index('ix_announcements_course', 'course_id'),
        Index('ix_announcements_target_type', 'target_type'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    created_by_user = relationship(
        "User",
        back_populates="announcements_created",
        foreign_keys=[created_by]
    )
    
    reads = relationship(
        "AnnouncementRead",
        back_populates="announcement",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Announcement {self.id}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_draft_announcement(self) -> bool:
        """Check if announcement is draft."""
        return self.status == AnnouncementStatus.DRAFT.value
    
    @property
    def is_published_announcement(self) -> bool:
        """Check if announcement is published."""
        return self.status == AnnouncementStatus.PUBLISHED.value
    
    @property
    def is_archived_announcement(self) -> bool:
        """Check if announcement is archived."""
        return self.status == AnnouncementStatus.ARCHIVED.value
    
    @property
    def is_expired_announcement(self) -> bool:
        """Check if announcement is expired."""
        if self.expires_at is None:
            return False
        return self.expires_at <= func.now() or self.status == AnnouncementStatus.EXPIRED.value
    
    @property
    def is_deleted_announcement(self) -> bool:
        """Check if announcement is deleted."""
        return self.status == AnnouncementStatus.DELETED.value
    
    @property
    def is_urgent(self) -> bool:
        """Check if announcement is urgent."""
        return self.priority == AnnouncementPriority.URGENT.value
    
    @property
    def is_high_priority(self) -> bool:
        """Check if announcement has high priority."""
        return self.priority in [AnnouncementPriority.HIGH.value, AnnouncementPriority.URGENT.value]
    
    @property
    def is_scheduled(self) -> bool:
        """Check if announcement is scheduled."""
        return self.scheduled_at is not None
    
    @property
    def is_published_and_active(self) -> bool:
        """Check if announcement is published and not expired."""
        return self.is_published_announcement and not self.is_expired_announcement
    
    @property
    def display_priority(self) -> str:
        """Get human-readable priority."""
        priority_map = {
            "low": "🟢 Low",
            "normal": "🔵 Normal",
            "high": "🟠 High",
            "urgent": "🔴 Urgent",
        }
        return priority_map.get(self.priority, "Normal")
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_draft_announcement:
            return "📝 Draft"
        elif self.is_published_announcement:
            return "📢 Published"
        elif self.is_archived_announcement:
            return "📦 Archived"
        elif self.is_expired_announcement:
            return "⏰ Expired"
        elif self.is_deleted_announcement:
            return "🗑️ Deleted"
        return "Unknown"
    
    @property
    def display_target(self) -> str:
        """Get human-readable target."""
        if self.target_type == AnnouncementTargetType.ALL_USERS.value:
            return "📢 All Users"
        elif self.target_type == AnnouncementTargetType.STUDENTS.value:
            return "🎓 Students"
        elif self.target_type == AnnouncementTargetType.TEACHERS.value:
            return "👨‍🏫 Teachers"
        elif self.target_type == AnnouncementTargetType.ADMINS.value:
            return "🛡️ Admins"
        elif self.target_type == AnnouncementTargetType.COURSE_SPECIFIC.value:
            return f"📚 Course Specific"
        elif self.target_type == AnnouncementTargetType.ROLE_SPECIFIC.value:
            return f"👥 Role Specific"
        return "Unknown"
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiry."""
        if self.expires_at is None:
            return -1
        if self.is_expired_announcement:
            return 0
        delta = self.expires_at - func.now()
        return max(0, delta.days)
    
    @property
    def read_rate(self) -> float:
        """Calculate read rate."""
        # This would need total users count
        return 0.0  # Placeholder
    
    @property
    def is_for_all_users(self) -> bool:
        """Check if announcement is for all users."""
        return self.target_type == AnnouncementTargetType.ALL_USERS.value
    
    @property
    def is_for_specific_course(self) -> bool:
        """Check if announcement is for a specific course."""
        return self.target_type == AnnouncementTargetType.COURSE_SPECIFIC.value and self.course_id is not None
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def publish(self) -> None:
        """Publish the announcement."""
        self.status = AnnouncementStatus.PUBLISHED.value
        self.published_at = func.now()
    
    def archive(self) -> None:
        """Archive the announcement."""
        self.status = AnnouncementStatus.ARCHIVED.value
    
    def expire(self) -> None:
        """Mark announcement as expired."""
        self.status = AnnouncementStatus.EXPIRED.value
        self.expires_at = func.now()
    
    def soft_delete_announcement(self) -> None:
        """Soft delete the announcement."""
        self.status = AnnouncementStatus.DELETED.value
        self.deleted_at = func.now()
    
    def restore_announcement(self) -> None:
        """Restore a soft-deleted announcement."""
        self.status = AnnouncementStatus.DRAFT.value
        self.deleted_at = None
    
    def schedule(self, scheduled_at: DateTime) -> None:
        """Schedule announcement for future publishing."""
        self.scheduled_at = scheduled_at
        self.status = AnnouncementStatus.DRAFT.value
    
    def unschedule(self) -> None:
        """Unschedule announcement."""
        self.scheduled_at = None
    
    def increment_view(self) -> None:
        """Increment view count."""
        self.views_count += 1
    
    def increment_read(self) -> None:
        """Increment read count."""
        self.read_count += 1
    
    def increment_click(self) -> None:
        """Increment click count."""
        self.click_count += 1
    
    def set_target_courses(self, course_ids: list) -> None:
        """Set target courses for announcement."""
        self.target_courses = course_ids
        self.target_type = AnnouncementTargetType.COURSE_SPECIFIC.value
    
    def set_target_roles(self, roles: list) -> None:
        """Set target roles for announcement."""
        self.target_roles = roles
        self.target_type = AnnouncementTargetType.ROLE_SPECIFIC.value
    
    def set_target_users(self, user_ids: list) -> None:
        """Set target users for announcement."""
        self.target_users = user_ids
    
    def set_priority(self, priority: str) -> None:
        """Set announcement priority."""
        if priority in [p.value for p in AnnouncementPriority]:
            self.priority = priority
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # TARGET CHECK METHODS
    # ============================================================
    
    def is_targeted_for_user(self, user_id: int, user_role: str, course_ids: list = None) -> bool:
        """
        Check if announcement is targeted for a specific user.
        
        Args:
            user_id: User ID to check
            user_role: User role (student, teacher, admin)
            course_ids: List of course IDs the user is enrolled in
        
        Returns:
            True if announcement is targeted for user
        """
        # Check deleted announcements
        if self.is_deleted_announcement:
            return False
        
        # Check if announcement is active
        if not self.is_published_and_active:
            return False
        
        # Check all users
        if self.is_for_all_users:
            return True
        
        # Check role-specific
        if self.target_type == AnnouncementTargetType.ROLE_SPECIFIC.value:
            if self.target_roles and user_role in self.target_roles:
                return True
        
        # Check course-specific
        if self.target_type == AnnouncementTargetType.COURSE_SPECIFIC.value:
            if self.course_id and course_ids and self.course_id in course_ids:
                return True
            if self.target_courses and course_ids:
                for course_id in course_ids:
                    if course_id in self.target_courses:
                        return True
        
        # Check specific users
        if self.target_users and user_id in self.target_users:
            return True
        
        return False
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert announcement to dictionary."""
        data = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "short_content": self.short_content,
            "priority": self.priority,
            "display_priority": self.display_priority,
            "status": self.status,
            "display_status": self.display_status,
            "target_type": self.target_type,
            "display_target": self.display_target,
            "is_for_all_users": self.is_for_all_users,
            "is_urgent": self.is_urgent,
            "is_published": self.is_published_announcement,
            "is_expired": self.is_expired_announcement,
            "is_scheduled": self.is_scheduled,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "days_until_expiry": self.days_until_expiry,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "views_count": self.views_count,
            "read_count": self.read_count,
            "click_count": self.click_count,
            "icon": self.icon,
            "banner_image_url": self.banner_image_url,
            "bg_color": self.bg_color,
            "text_color": self.text_color,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "target_roles": self.target_roles,
                "target_courses": self.target_courses,
                "target_users": self.target_users,
                "course_id": self.course_id,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing announcement data."""
        data = self.to_dict()
        data.pop("target_roles", None)
        data.pop("target_courses", None)
        data.pop("target_users", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing announcement data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. ANNOUNCEMENT READ MODEL
# ============================================================

class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    announcement_id = Column(Integer, ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # READ DETAILS
    # ============================================================
    read_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # NEW: Read duration (in seconds)
    read_duration_seconds = Column(Integer, nullable=True)
    
    # NEW: Device info
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)
    
    # NEW: Notified via
    notification_method = Column(String(50), nullable=True)  # email, push, in_app
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_announcement_reads_unique', 'announcement_id', 'user_id', unique=True),
        Index('ix_announcement_reads_announcement', 'announcement_id'),
        Index('ix_announcement_reads_user', 'user_id'),
        Index('ix_announcement_reads_read_at', 'read_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    announcement = relationship(
        "Announcement",
        back_populates="reads",
        foreign_keys=[announcement_id]
    )
    
    user = relationship(
        "User",
        back_populates="announcement_reads",
        foreign_keys=[user_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<AnnouncementRead {self.id}: {self.user_id} -> {self.announcement_id}>"
    
    def to_dict(self) -> dict:
        """Convert announcement read to dictionary."""
        return {
            "id": self.id,
            "announcement_id": self.announcement_id,
            "user_id": self.user_id,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "read_duration_seconds": self.read_duration_seconds,
            "device_type": self.device_type,
            "notification_method": self.notification_method,
        }


# ============================================================
# 3. ANNOUNCEMENT TEMPLATE (For reusable announcements)
# ============================================================

class AnnouncementTemplate(Base):
    """Pre-defined announcement templates."""
    __tablename__ = "announcement_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    
    # Content
    title_template = Column(String(255), nullable=False)
    content_template = Column(Text, nullable=False)
    short_content_template = Column(String(200), nullable=True)
    
    # Defaults
    default_priority = Column(String(20), default=AnnouncementPriority.NORMAL.value, nullable=False)
    default_target_type = Column(String(50), default=AnnouncementTargetType.ALL_USERS.value, nullable=False)
    default_icon = Column(String(50), nullable=True)
    default_bg_color = Column(String(7), nullable=True)
    default_text_color = Column(String(7), nullable=True)
    
    # Placeholders
    placeholders = Column(JSON, nullable=True)
    # Example: ["student_name", "course_name", "teacher_name"]
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # Can't be deleted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<AnnouncementTemplate {self.name}>"
    
    def render_title(self, context: dict) -> str:
        """Render title with placeholders."""
        result = self.title_template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    def render_content(self, context: dict) -> str:
        """Render content with placeholders."""
        result = self.content_template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    def render_short_content(self, context: dict) -> str:
        """Render short content with placeholders."""
        if self.short_content_template is None:
            return self.render_content(context)[:200]
        result = self.short_content_template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result