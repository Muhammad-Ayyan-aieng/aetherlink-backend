# ============================================================
# AETHER LINK - COURSE MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class CourseStatus(str, enum.Enum):
    """Course status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


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
    
    # ============================================================
    # PRICING & MEDIA
    # ============================================================
    price = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    thumbnail = Column(String(500), nullable=True)
    
    # ============================================================
    # TEACHER
    # ============================================================
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ============================================================
    # METADATA
    # ============================================================
    total_sessions = Column(Integer, default=0, nullable=False)
    status = Column(
        SQLEnum(CourseStatus, values_callable=lambda x: [e.value for e in x]),
        default=CourseStatus.DRAFT,
        nullable=False
    )
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # SEO FIELDS
    # ============================================================
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    # Teacher
    teacher = relationship(
        "User",
        back_populates="taught_courses",
        foreign_keys=[teacher_id]
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
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Course {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # HELPER METHODS
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
    
    def publish(self) -> None:
        """Publish the course."""
        self.status = CourseStatus.PUBLISHED
    
    def archive(self) -> None:
        """Archive the course."""
        self.status = CourseStatus.ARCHIVED
    
    def draft(self) -> None:
        """Move course to draft."""
        self.status = CourseStatus.DRAFT
    
    def soft_delete(self) -> None:
        """Soft delete the course."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted course."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION (Future - used in schemas)
    # ============================================================
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """Validate price is within limits."""
        return 0 <= price <= 999999
    
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate slug format."""
        import re
        return bool(re.match(r'^[a-z0-9-]+$', slug))
