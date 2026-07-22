# ============================================================
# AETHER LINK - LEARNING PATH MODEL
# ============================================================
# Purpose: Group courses into structured learning paths
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class LearningPathStatus(str, enum.Enum):
    """Learning path status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LearningPathLevel(str, enum.Enum):
    """Learning path level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class PathEnrollmentStatus(str, enum.Enum):
    """Path enrollment status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"


# ============================================================
# 1. LEARNING PATH MODEL
# ============================================================

class LearningPath(Base):
    __tablename__ = "learning_paths"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(200), nullable=True)
    
    # ============================================================
    # MEDIA & PRICING
    # ============================================================
    thumbnail = Column(String(500), nullable=True)
    banner_image = Column(String(500), nullable=True)
    
    # NEW: Pricing (can be different from sum of courses)
    price = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    original_price = Column(DECIMAL(10, 2), nullable=True)  # For discounts
    
    # NEW: Currency
    currency = Column(String(3), default="PKR", nullable=False)
    
    # ============================================================
    # METADATA
    # ============================================================
    level = Column(
        String(50),
        default=LearningPathLevel.ALL_LEVELS.value,
        nullable=False
    )
    
    # NEW: Category
    category = Column(String(100), nullable=True)
    
    # NEW: Estimated duration
    estimated_duration_hours = Column(Integer, nullable=True)
    estimated_duration_weeks = Column(Integer, nullable=True)
    
    # NEW: Difficulty score (1-10)
    difficulty = Column(Integer, default=5, nullable=False)
    
    # ============================================================
    # SKILLS & OUTCOMES
    # ============================================================
    skills_covered = Column(JSON, nullable=True)  # ["Python", "FastAPI", "PostgreSQL"]
    learning_outcomes = Column(JSON, nullable=True)  # ["Build REST APIs", "Deploy applications"]
    prerequisites = Column(JSON, nullable=True)  # ["Basic programming", "Understanding of databases"]
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=LearningPathStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # STATISTICS (Cached)
    # ============================================================
    total_courses = Column(Integer, default=0, nullable=False)
    total_students = Column(Integer, default=0, nullable=False)
    completion_rate = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    average_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # CREATOR
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # METADATA
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
        Index('ix_learning_paths_slug', 'slug'),
        Index('ix_learning_paths_status', 'status'),
        Index('ix_learning_paths_level', 'level'),
        Index('ix_learning_paths_featured', 'is_featured'),
        Index('ix_learning_paths_published', 'is_published'),
        Index('ix_learning_paths_created', 'created_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        uselist=False
    )
    
    # NEW: Courses in this path (ordered)
    path_courses = relationship(
        "PathCourse",
        back_populates="learning_path",
        cascade="all, delete-orphan",
        order_by="PathCourse.order_index"
    )
    
    # NEW: Enrollments in this path
    enrollments = relationship(
        "PathEnrollment",
        back_populates="learning_path",
        cascade="all, delete-orphan"
    )
    
    # NEW: Reviews for this path
    reviews = relationship(
        "PathReview",
        back_populates="learning_path",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<LearningPath {self.id}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_draft_path(self) -> bool:
        """Check if learning path is draft."""
        return self.status == LearningPathStatus.DRAFT.value
    
    @property
    def is_published_path(self) -> bool:
        """Check if learning path is published."""
        return self.status == LearningPathStatus.PUBLISHED.value
    
    @property
    def is_archived_path(self) -> bool:
        """Check if learning path is archived."""
        return self.status == LearningPathStatus.ARCHIVED.value
    
    @property
    def is_active_path(self) -> bool:
        """Check if learning path is active (published and not deleted)."""
        return self.is_published_path and self.deleted_at is None
    
    @property
    def display_level(self) -> str:
        """Get human-readable level."""
        level_map = {
            "beginner": "🌟 Beginner",
            "intermediate": "🚀 Intermediate",
            "advanced": "🏆 Advanced",
            "all_levels": "📚 All Levels",
        }
        return level_map.get(self.level, "All Levels")
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_draft_path:
            return "📝 Draft"
        elif self.is_published_path:
            return "📢 Published"
        elif self.is_archived_path:
            return "📦 Archived"
        return "Unknown"
    
    @property
    def total_courses_count(self) -> int:
        """Get total courses in this path."""
        return len(self.path_courses) if self.path_courses else 0
    
    @property
    def courses_list(self) -> list:
        """Get list of courses in this path."""
        if not self.path_courses:
            return []
        return [pc.course_id for pc in self.path_courses if pc.course]
    
    @property
    def first_course(self):
        """Get first course in the path."""
        if not self.path_courses:
            return None
        return self.path_courses[0].course if self.path_courses[0].course else None
    
    @property
    def last_course(self):
        """Get last course in the path."""
        if not self.path_courses:
            return None
        return self.path_courses[-1].course if self.path_courses[-1].course else None
    
    @property
    def is_complete_path(self) -> bool:
        """Check if all courses in path are complete."""
        # This would need student-specific logic
        return False  # Placeholder
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def publish(self) -> None:
        """Publish the learning path."""
        self.status = LearningPathStatus.PUBLISHED.value
        self.is_published = True
        self.published_at = func.now()
    
    def archive(self) -> None:
        """Archive the learning path."""
        self.status = LearningPathStatus.ARCHIVED.value
        self.is_published = False
    
    def unpublish(self) -> None:
        """Unpublish the learning path."""
        self.status = LearningPathStatus.DRAFT.value
        self.is_published = False
        self.published_at = None
    
    def soft_delete_path(self) -> None:
        """Soft delete the learning path."""
        self.deleted_at = func.now()
        self.is_published = False
    
    def restore_path(self) -> None:
        """Restore a soft-deleted learning path."""
        self.deleted_at = None
    
    def increment_student_count(self) -> None:
        """Increment total students count."""
        self.total_students += 1
    
    def decrement_student_count(self) -> None:
        """Decrement total students count."""
        if self.total_students > 0:
            self.total_students -= 1
    
    def update_completion_rate(self, completed: int, total: int) -> None:
        """Update completion rate."""
        if total == 0:
            self.completion_rate = 0.00
        else:
            self.completion_rate = (completed / total) * 100
    
    def update_rating(self, new_rating: float) -> None:
        """Update average rating with a new review."""
        total = self.average_rating * self.total_reviews
        self.total_reviews += 1
        if self.total_reviews > 0:
            self.average_rating = (total + new_rating) / self.total_reviews
    
    def set_skill_tags(self, skills: list) -> None:
        """Set skill tags for the learning path."""
        self.skills_covered = skills
    
    def set_learning_outcomes(self, outcomes: list) -> None:
        """Set learning outcomes for the learning path."""
        self.learning_outcomes = outcomes
    
    def set_prerequisites(self, prerequisites: list) -> None:
        """Set prerequisites for the learning path."""
        self.prerequisites = prerequisites
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert learning path to dictionary."""
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "thumbnail": self.thumbnail,
            "banner_image": self.banner_image,
            "price": float(self.price) if self.price else 0.0,
            "original_price": float(self.original_price) if self.original_price else None,
            "currency": self.currency,
            "level": self.level,
            "display_level": self.display_level,
            "category": self.category,
            "estimated_duration_hours": self.estimated_duration_hours,
            "estimated_duration_weeks": self.estimated_duration_weeks,
            "difficulty": self.difficulty,
            "skills_covered": self.skills_covered,
            "learning_outcomes": self.learning_outcomes,
            "prerequisites": self.prerequisites,
            "status": self.status,
            "display_status": self.display_status,
            "is_featured": self.is_featured,
            "is_published": self.is_published,
            "is_active": self.is_active_path,
            "total_courses": self.total_courses,
            "total_students": self.total_students,
            "completion_rate": float(self.completion_rate) if self.completion_rate else 0.0,
            "average_rating": float(self.average_rating) if self.average_rating else 0.0,
            "total_reviews": self.total_reviews,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing learning path data."""
        data = self.to_dict()
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing learning path data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. PATH COURSE MODEL (Many-to-Many with order)
# ============================================================

class PathCourse(Base):
    __tablename__ = "path_courses"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    path_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # ORDERING
    # ============================================================
    order_index = Column(Integer, nullable=False, default=0)
    
    # NEW: Section/Chapter grouping
    section = Column(String(100), nullable=True)
    
    # NEW: Is this course optional?
    is_optional = Column(Boolean, default=False, nullable=False)
    
    # NEW: Custom description for this course in the path
    custom_description = Column(Text, nullable=True)
    
    # NEW: Estimated days to complete this course
    estimated_days = Column(Integer, nullable=True)
    
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
        Index('ix_path_courses_unique', 'path_id', 'course_id', unique=True),
        Index('ix_path_courses_path_order', 'path_id', 'order_index'),
        Index('ix_path_courses_path', 'path_id'),
        Index('ix_path_courses_course', 'course_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    learning_path = relationship(
        "LearningPath",
        back_populates="path_courses",
        foreign_keys=[path_id]
    )
    
    course = relationship(
        "Course",
        foreign_keys=[course_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<PathCourse {self.id}: {self.path_id} -> {self.course_id}>"
    
    def to_dict(self) -> dict:
        """Convert path course to dictionary."""
        return {
            "id": self.id,
            "path_id": self.path_id,
            "course_id": self.course_id,
            "course_title": self.course.title if self.course else None,
            "order_index": self.order_index,
            "section": self.section,
            "is_optional": self.is_optional,
            "custom_description": self.custom_description,
            "estimated_days": self.estimated_days,
        }


# ============================================================
# 3. PATH ENROLLMENT MODEL
# ============================================================

class PathEnrollment(Base):
    __tablename__ = "path_enrollments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    path_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=PathEnrollmentStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # PROGRESS
    # ============================================================
    progress_percentage = Column(Integer, default=0, nullable=False)
    completed_courses = Column(Integer, default=0, nullable=False)
    total_courses = Column(Integer, default=0, nullable=False)
    
    # NEW: Current course in the path
    current_course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Course completion tracking
    completed_course_ids = Column(JSON, nullable=True)  # List of completed course IDs
    
    # ============================================================
    # PAYMENT
    # ============================================================
    payment_amount = Column(DECIMAL(10, 2), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_verified = Column(Boolean, default=False, nullable=False)
    payment_verified_at = Column(DateTime(timezone=True), nullable=True)
    payment_verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # DATES
    # ============================================================
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    dropped_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Last accessed
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # METADATA
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
        Index('ix_path_enrollments_unique', 'path_id', 'student_id', unique=True),
        Index('ix_path_enrollments_path', 'path_id'),
        Index('ix_path_enrollments_student', 'student_id'),
        Index('ix_path_enrollments_status', 'status'),
        Index('ix_path_enrollments_current_course', 'current_course_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    learning_path = relationship(
        "LearningPath",
        back_populates="enrollments",
        foreign_keys=[path_id]
    )
    
    student = relationship(
        "User",
        back_populates="path_enrollments",
        foreign_keys=[student_id]
    )
    
    current_course = relationship(
        "Course",
        foreign_keys=[current_course_id]
    )
    
    payment_verified_by_user = relationship(
        "User",
        foreign_keys=[payment_verified_by],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<PathEnrollment {self.id}: {self.student_id} -> {self.path_id}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_pending_path(self) -> bool:
        """Check if enrollment is pending."""
        return self.status == PathEnrollmentStatus.PENDING.value
    
    @property
    def is_active_path(self) -> bool:
        """Check if enrollment is active."""
        return self.status == PathEnrollmentStatus.ACTIVE.value
    
    @property
    def is_completed_path(self) -> bool:
        """Check if enrollment is completed."""
        return self.status == PathEnrollmentStatus.COMPLETED.value
    
    @property
    def is_dropped_path(self) -> bool:
        """Check if enrollment is dropped."""
        return self.status == PathEnrollmentStatus.DROPPED.value
    
    @property
    def is_expired_path(self) -> bool:
        """Check if enrollment is expired."""
        return self.status == PathEnrollmentStatus.EXPIRED.value
    
    @property
    def is_fully_completed(self) -> bool:
        """Check if all courses in path are completed."""
        return self.total_courses > 0 and self.completed_courses >= self.total_courses
    
    @property
    def next_course_id(self) -> int:
        """Get the next course ID to complete."""
        if not self.learning_path or not self.learning_path.path_courses:
            return None
        
        for pc in self.learning_path.path_courses:
            if pc.course_id not in (self.completed_course_ids or []):
                return pc.course_id
        return None
    
    @property
    def has_next_course(self) -> bool:
        """Check if there's a next course."""
        return self.next_course_id is not None
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def activate(self, payment_verified_by: int = None) -> None:
        """Activate path enrollment."""
        self.status = PathEnrollmentStatus.ACTIVE.value
        if payment_verified_by:
            self.payment_verified = True
            self.payment_verified_by = payment_verified_by
            self.payment_verified_at = func.now()
        
        # Get total courses in path
        if self.learning_path:
            self.total_courses = len(self.learning_path.path_courses) if self.learning_path.path_courses else 0
    
    def complete_course(self, course_id: int) -> None:
        """Mark a course as completed in the path."""
        if self.completed_course_ids is None:
            self.completed_course_ids = []
        
        if course_id not in self.completed_course_ids:
            self.completed_course_ids.append(course_id)
            self.completed_courses += 1
            
            # Update progress
            if self.total_courses > 0:
                self.progress_percentage = int((self.completed_courses / self.total_courses) * 100)
            
            # Check if path is complete
            if self.is_fully_completed:
                self.complete_path()
    
    def complete_path(self) -> None:
        """Mark entire path as completed."""
        self.status = PathEnrollmentStatus.COMPLETED.value
        self.completed_at = func.now()
        self.progress_percentage = 100
    
    def drop_path(self) -> None:
        """Drop the path enrollment."""
        self.status = PathEnrollmentStatus.DROPPED.value
        self.dropped_at = func.now()
    
    def expire_path(self) -> None:
        """Expire the path enrollment."""
        self.status = PathEnrollmentStatus.EXPIRED.value
    
    def update_last_accessed(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed_at = func.now()
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete_path_enrollment(self) -> None:
        """Soft delete the path enrollment."""
        self.deleted_at = func.now()
    
    def restore_path_enrollment(self) -> None:
        """Restore a soft-deleted path enrollment."""
        self.deleted_at = None
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert path enrollment to dictionary."""
        data = {
            "id": self.id,
            "path_id": self.path_id,
            "path_title": self.learning_path.title if self.learning_path else None,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "completed_courses": self.completed_courses,
            "total_courses": self.total_courses,
            "is_fully_completed": self.is_fully_completed,
            "has_next_course": self.has_next_course,
            "next_course_id": self.next_course_id,
            "current_course_id": self.current_course_id,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "payment_amount": float(self.payment_amount) if self.payment_amount else None,
                "payment_method": self.payment_method,
                "payment_verified": self.payment_verified,
                "payment_verified_at": self.payment_verified_at.isoformat() if self.payment_verified_at else None,
                "payment_verified_by": self.payment_verified_by,
                "completed_course_ids": self.completed_course_ids,
                "dropped_at": self.dropped_at.isoformat() if self.dropped_at else None,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing path enrollment data."""
        data = self.to_dict()
        data.pop("payment_verified_by", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing path enrollment data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 4. PATH REVIEW MODEL
# ============================================================

class PathReview(Base):
    """Reviews for learning paths."""
    __tablename__ = "path_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    
    is_verified = Column(Boolean, default=False, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    
    status = Column(String(20), default="approved", nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    learning_path = relationship("LearningPath", back_populates="reviews")
    student = relationship("User", foreign_keys=[student_id])
    
    __table_args__ = (
        Index('ix_path_reviews_path_student', 'path_id', 'student_id', unique=True),
        Index('ix_path_reviews_path', 'path_id'),
        Index('ix_path_reviews_student', 'student_id'),
        Index('ix_path_reviews_rating', 'rating'),
    )
    
    def __repr__(self) -> str:
        return f"<PathReview {self.id}: {self.rating}⭐ - {self.learning_path.title if self.learning_path else 'Unknown'}>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path_id": self.path_id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else "Anonymous",
            "is_anonymous": self.is_anonymous,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "is_verified": self.is_verified,
            "helpful_count": self.helpful_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }