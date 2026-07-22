# ============================================================
# AETHER LINK - COURSE MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, Enum as SQLEnum, ForeignKey, DateTime, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import re
from ..core.database import Base


class CourseStatus(str, enum.Enum):
    """Course status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseLevel(str, enum.Enum):  # NEW
    """Course level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class CourseCategory(str, enum.Enum):  # NEW
    """Course category enumeration."""
    PROGRAMMING = "programming"
    DESIGN = "design"
    BUSINESS = "business"
    MARKETING = "marketing"
    DATA_SCIENCE = "data_science"
    AI_ML = "ai_ml"
    LANGUAGE = "language"
    PERSONAL_DEVELOPMENT = "personal_development"
    OTHER = "other"


class Course(Base):
    __tablename__ = "courses"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # NEW: Short description for listings
    short_description = Column(String(200), nullable=True)
    
    # ============================================================
    # PRICING & MEDIA
    # ============================================================
    price = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    thumbnail = Column(String(500), nullable=True)
    
    # NEW: Level & Category (for filtering)
    level = Column(String(50), nullable=True)  # CourseLevel enum
    category = Column(String(100), nullable=True)  # CourseCategory enum
    
    # ============================================================
    # TEACHER (SINGLE PRIMARY TEACHER)
    # ============================================================
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Note: Multiple teachers per course handled by course_teachers table
    
    # ============================================================
    # NEW: CREATED BY (Admin who created the course)
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # ============================================================
    # METADATA
    # ============================================================
    total_sessions = Column(Integer, default=0, nullable=False)
    
    # NEW: Duration in weeks
    duration_weeks = Column(Integer, default=0, nullable=False)
    
    status = Column(
        SQLEnum(CourseStatus, values_callable=lambda x: [e.value for e in x]),
        default=CourseStatus.DRAFT,
        nullable=False
    )
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # NEW: Publication status with timestamp
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # SEO FIELDS
    # ============================================================
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    
    # ============================================================
    # NEW: COURSE STATISTICS (Cached for performance)
    # ============================================================
    total_students_enrolled = Column(Integer, default=0, nullable=False)
    total_completed = Column(Integer, default=0, nullable=False)
    average_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # NEW: PREREQUISITES & REQUIREMENTS
    # ============================================================
    prerequisites = Column(JSON, nullable=True)  # List of prerequisite courses or skills
    # Example: ["Basic Python knowledge", "Understanding of databases"]
    
    learning_objectives = Column(JSON, nullable=True)  # List of learning objectives
    # Example: ["Build REST APIs", "Deploy to production"]
    
    # ============================================================
    # NEW: CERTIFICATE SETTINGS
    # ============================================================
    certificate_enabled = Column(Boolean, default=True, nullable=False)
    certificate_template_id = Column(Integer, ForeignKey("certificate_templates.id"), nullable=True)
    
    # ============================================================
    # NEW: SETTINGS & CONFIGURATION
    # ============================================================
    settings = Column(JSON, nullable=True)
    # Example: {"attendance_threshold": 60, "video_watch_threshold": 80}
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # Teacher (Primary teacher)
    teacher = relationship(
        "User",
        back_populates="taught_courses",
        foreign_keys=[teacher_id]
    )
    
    # NEW: Created by (Admin)
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        uselist=False
    )
    
    # NEW: Multiple teachers (many-to-many via course_teachers)
    teachers = relationship(
        "CourseTeacher",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # Sessions
    sessions = relationship(
        "Session",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # Enrollments
    enrollments = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # NEW: Materials
    materials = relationship(
        "Material",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # NEW: Reviews
    reviews = relationship(
        "Review",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # NEW: Assignments
    assignments = relationship(
        "Assignment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # NEW: Learning Paths (many-to-many via path_courses)
    paths = relationship(
        "PathCourse",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # NEW: Announcements targeting this course
    announcements = relationship(
        "Announcement",
        foreign_keys="Announcement.target_courses",
        viewonly=True
    )
    
    # NEW: Teacher Invitations
    teacher_invitations = relationship(
        "TeacherInvitation",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    # NEW: Certificate Template
    certificate_template = relationship(
        "CertificateTemplate",
        foreign_keys=[certificate_template_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Course {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_published(self) -> bool:
        """Check if course is published."""
        return self.status == CourseStatus.PUBLISHED
    
    @property
    def is_draft(self) -> bool:
        """Check if course is draft."""
        return self.status == CourseStatus.DRAFT
    
    @property
    def is_archived(self) -> bool:
        """Check if course is archived."""
        return self.status == CourseStatus.ARCHIVED
    
    @property
    def is_free(self) -> bool:
        """Check if course is free."""
        return self.price == 0
    
    @property
    def is_active(self) -> bool:
        """Check if course is active (published and not deleted)."""
        return self.is_published and self.deleted_at is None
    
    @property
    def has_certificate(self) -> bool:
        """Check if course offers a certificate."""
        return self.certificate_enabled
    
    @property
    def display_price(self) -> str:
        """Get formatted price string."""
        if self.is_free:
            return "Free"
        return f"${self.price:.2f}"
    
    @property
    def level_display(self) -> str:
        """Get human-readable level name."""
        level_map = {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced",
            "all_levels": "All Levels",
        }
        return level_map.get(self.level, self.level or "Not Specified")
    
    @property
    def category_display(self) -> str:
        """Get human-readable category name."""
        category_map = {
            "programming": "Programming",
            "design": "Design",
            "business": "Business",
            "marketing": "Marketing",
            "data_science": "Data Science",
            "ai_ml": "AI & Machine Learning",
            "language": "Language",
            "personal_development": "Personal Development",
            "other": "Other",
        }
        return category_map.get(self.category, self.category or "Not Specified")
    
    @property
    def completion_rate(self) -> float:
        """Calculate course completion rate."""
        if self.total_students_enrolled == 0:
            return 0.0
        return (self.total_completed / self.total_students_enrolled) * 100
    
    @property
    def is_featured_course(self) -> bool:
        """Check if course is featured."""
        return self.is_featured and self.is_published
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def publish(self) -> None:
        """Publish the course."""
        self.status = CourseStatus.PUBLISHED
        self.is_published = True
        self.published_at = func.now()
    
    def archive(self) -> None:
        """Archive the course."""
        self.status = CourseStatus.ARCHIVED
        self.is_published = False
    
    def unpublish(self) -> None:
        """Unpublish the course (move to draft)."""
        self.status = CourseStatus.DRAFT
        self.is_published = False
        self.published_at = None
    
    def draft(self) -> None:
        """Move course to draft."""
        self.status = CourseStatus.DRAFT
        self.is_published = False
    
    def soft_delete(self) -> None:
        """Soft delete the course."""
        self.deleted_at = func.now()
        self.is_published = False
    
    def restore(self) -> None:
        """Restore a soft-deleted course."""
        self.deleted_at = None
    
    # NEW: Stats update methods
    def increment_student_count(self) -> None:
        """Increment enrolled students count."""
        self.total_students_enrolled += 1
    
    def decrement_student_count(self) -> None:
        """Decrement enrolled students count."""
        if self.total_students_enrolled > 0:
            self.total_students_enrolled -= 1
    
    def increment_completed_count(self) -> None:
        """Increment completed students count."""
        self.total_completed += 1
    
    def update_rating(self, new_rating: float) -> None:
        """Update average rating with a new review."""
        # This is a simplified version - actual calculation should be in service
        total = self.average_rating * self.total_reviews
        self.total_reviews += 1
        self.average_rating = (total + new_rating) / self.total_reviews
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """Validate price is within limits."""
        return 0 <= price <= 999999
    
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate slug format."""
        return bool(re.match(r'^[a-z0-9-]+$', slug))
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate title length."""
        return 3 <= len(title) <= 255
    
    @staticmethod
    def validate_level(level: str) -> bool:
        """Validate level is valid."""
        valid_levels = [e.value for e in CourseLevel]
        return level in valid_levels if level else True
    
    @staticmethod
    def validate_category(category: str) -> bool:
        """Validate category is valid."""
        valid_categories = [e.value for e in CourseCategory]
        return category in valid_categories if category else True
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert course to dictionary."""
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "short_description": self.short_description,
            "description": self.description,
            "price": float(self.price),
            "display_price": self.display_price,
            "is_free": self.is_free,
            "thumbnail": self.thumbnail,
            "level": self.level,
            "level_display": self.level_display,
            "category": self.category,
            "category_display": self.category_display,
            "status": self.status.value if self.status else None,
            "is_published": self.is_published,
            "is_featured": self.is_featured,
            "is_active": self.is_active,
            "teacher_id": self.teacher_id,
            "total_sessions": self.total_sessions,
            "duration_weeks": self.duration_weeks,
            "total_students_enrolled": self.total_students_enrolled,
            "total_completed": self.total_completed,
            "average_rating": float(self.average_rating) if self.average_rating else 0.0,
            "total_reviews": self.total_reviews,
            "completion_rate": self.completion_rate,
            "certificate_enabled": self.certificate_enabled,
            "prerequisites": self.prerequisites,
            "learning_objectives": self.learning_objectives,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "meta_title": self.meta_title,
                "meta_description": self.meta_description,
                "meta_keywords": self.meta_keywords,
                "settings": self.settings,
                "certificate_template_id": self.certificate_template_id,
                "created_by": self.created_by,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing course data (safe for any response)."""
        data = self.to_dict()
        # Remove internal fields for public view
        data.pop("status", None)
        data.pop("created_by", None)
        data.pop("certificate_template_id", None)
        data.pop("settings", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing course data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: COURSE TEACHER (Many-to-Many)
# ============================================================

class CourseTeacher(Base):
    """Many-to-many relationship between courses and teachers."""
    __tablename__ = "course_teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Additional metadata
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # NEW: Role within the course
    role = Column(String(50), nullable=True)  # primary, co-teacher, assistant
    
    # NEW: Custom permissions for this teacher in this course
    permissions = Column(JSON, nullable=True)
    # Example: {"can_grade": true, "can_upload_materials": true}
    
    # NEW: Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    course = relationship("Course", back_populates="teachers")
    teacher = relationship("User", foreign_keys=[teacher_id])
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    # Constraints
    __table_args__ = (
        # Prevent duplicate teacher-course assignments
        # This is handled at database level with unique constraint
    )
    
    @property
    def is_primary(self) -> bool:
        """Check if this teacher is the primary teacher."""
        return self.role == "primary"
    
    @property
    def can_grade(self) -> bool:
        """Check if teacher can grade assignments."""
        if self.permissions and "can_grade" in self.permissions:
            return self.permissions["can_grade"]
        return False
    
    @property
    def can_upload_materials(self) -> bool:
        """Check if teacher can upload materials."""
        if self.permissions and "can_upload_materials" in self.permissions:
            return self.permissions["can_upload_materials"]
        return True  # Default for teachers


# ============================================================
# NEW: COURSE STATS (Real-time stats view)
# ============================================================

class CourseStats(Base):
    """Real-time course statistics (view-only)."""
    __tablename__ = "course_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Enrollment stats
    total_students = Column(Integer, default=0, nullable=False)
    active_students = Column(Integer, default=0, nullable=False)
    completed_students = Column(Integer, default=0, nullable=False)
    
    # Engagement stats
    avg_attendance_rate = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    avg_session_completion = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    avg_time_spent_minutes = Column(Integer, default=0, nullable=False)
    
    # Revenue stats
    total_revenue = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    avg_revenue_per_student = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    
    # Review stats
    total_reviews = Column(Integer, default=0, nullable=False)
    avg_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    
    # Timestamp
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    course = relationship("Course")
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        return {
            "total_students": self.total_students,
            "active_students": self.active_students,
            "completed_students": self.completed_students,
            "avg_attendance_rate": float(self.avg_attendance_rate) if self.avg_attendance_rate else 0.0,
            "avg_session_completion": float(self.avg_session_completion) if self.avg_session_completion else 0.0,
            "avg_time_spent_minutes": self.avg_time_spent_minutes,
            "total_revenue": float(self.total_revenue) if self.total_revenue else 0.0,
            "avg_revenue_per_student": float(self.avg_revenue_per_student) if self.avg_revenue_per_student else 0.0,
            "total_reviews": self.total_reviews,
            "avg_rating": float(self.avg_rating) if self.avg_rating else 0.0,
        }