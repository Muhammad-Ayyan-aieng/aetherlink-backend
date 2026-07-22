# ============================================================
# AETHER LINK - LEARNING PATH SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# LEARNING PATH ENUMS
# ============================================================

class LearningPathStatusEnum(str, Enum):
    """Learning path status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LearningPathLevelEnum(str, Enum):
    """Learning path level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class PathEnrollmentStatusEnum(str, Enum):
    """Path enrollment status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"


# ============================================================
# BASE SCHEMA
# ============================================================

class LearningPathBase(BaseModel):
    """Base learning path schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# LEARNING PATH CREATE SCHEMA
# ============================================================

class LearningPathCreate(LearningPathBase):
    """Schema for creating a learning path."""
    
    title: str = Field(..., min_length=3, max_length=255, description="Learning path title")
    slug: str = Field(..., min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=5000, description="Learning path description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description for listings")
    
    thumbnail: Optional[str] = Field(default=None, max_length=500, description="Thumbnail URL")
    banner_image: Optional[str] = Field(default=None, max_length=500, description="Banner image URL")
    
    price: float = Field(default=0.0, ge=0, description="Learning path price")
    original_price: Optional[float] = Field(default=None, ge=0, description="Original price (for discounts)")
    currency: str = Field(default="PKR", max_length=3, description="Currency code")
    
    level: LearningPathLevelEnum = Field(
        default=LearningPathLevelEnum.ALL_LEVELS,
        description="Learning path level"
    )
    category: Optional[str] = Field(default=None, max_length=100, description="Category")
    
    estimated_duration_hours: Optional[int] = Field(default=None, ge=0, description="Estimated duration in hours")
    estimated_duration_weeks: Optional[int] = Field(default=None, ge=0, description="Estimated duration in weeks")
    difficulty: int = Field(default=5, ge=1, le=10, description="Difficulty score (1-10)")
    
    skills_covered: Optional[List[str]] = Field(default=None, description="Skills covered")
    learning_outcomes: Optional[List[str]] = Field(default=None, description="Learning outcomes")
    prerequisites: Optional[List[str]] = Field(default=None, description="Prerequisites")
    
    status: LearningPathStatusEnum = Field(
        default=LearningPathStatusEnum.DRAFT,
        description="Learning path status"
    )
    is_featured: bool = Field(default=False, description="Featured on homepage")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()


# ============================================================
# LEARNING PATH UPDATE SCHEMA
# ============================================================

class LearningPathUpdate(LearningPathBase):
    """Schema for updating a learning path."""
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Learning path title")
    slug: Optional[str] = Field(default=None, min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=5000, description="Learning path description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description")
    
    thumbnail: Optional[str] = Field(default=None, max_length=500, description="Thumbnail URL")
    banner_image: Optional[str] = Field(default=None, max_length=500, description="Banner image URL")
    
    price: Optional[float] = Field(default=None, ge=0, description="Learning path price")
    original_price: Optional[float] = Field(default=None, ge=0, description="Original price")
    
    level: Optional[LearningPathLevelEnum] = Field(default=None, description="Learning path level")
    category: Optional[str] = Field(default=None, max_length=100, description="Category")
    
    estimated_duration_hours: Optional[int] = Field(default=None, ge=0, description="Estimated duration in hours")
    estimated_duration_weeks: Optional[int] = Field(default=None, ge=0, description="Estimated duration in weeks")
    difficulty: Optional[int] = Field(default=None, ge=1, le=10, description="Difficulty score (1-10)")
    
    skills_covered: Optional[List[str]] = Field(default=None, description="Skills covered")
    learning_outcomes: Optional[List[str]] = Field(default=None, description="Learning outcomes")
    prerequisites: Optional[List[str]] = Field(default=None, description="Prerequisites")
    
    status: Optional[LearningPathStatusEnum] = Field(default=None, description="Learning path status")
    is_featured: Optional[bool] = Field(default=None, description="Featured on homepage")


# ============================================================
# PATH COURSE CREATE SCHEMA
# ============================================================

class PathCourseCreate(LearningPathBase):
    """Schema for adding a course to a learning path."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    order_index: int = Field(..., ge=0, description="Order in the path")
    
    # NEW: Section/Chapter grouping
    section: Optional[str] = Field(default=None, max_length=100, description="Section name")
    
    # NEW: Is this course optional?
    is_optional: bool = Field(default=False, description="Is this course optional?")
    
    # NEW: Custom description for this course in the path
    custom_description: Optional[str] = Field(default=None, max_length=500, description="Custom course description")
    
    # NEW: Estimated days to complete
    estimated_days: Optional[int] = Field(default=None, ge=0, description="Estimated days to complete")


class PathCourseUpdate(LearningPathBase):
    """Schema for updating a course in a learning path."""
    
    order_index: Optional[int] = Field(default=None, ge=0, description="Order in the path")
    section: Optional[str] = Field(default=None, max_length=100, description="Section name")
    is_optional: Optional[bool] = Field(default=None, description="Is this course optional?")
    custom_description: Optional[str] = Field(default=None, max_length=500, description="Custom course description")
    estimated_days: Optional[int] = Field(default=None, ge=0, description="Estimated days to complete")


# ============================================================
# PATH ENROLLMENT SCHEMAS
# ============================================================

class PathEnrollmentCreate(LearningPathBase):
    """Schema for enrolling in a learning path."""
    
    path_id: int = Field(..., gt=0, description="Learning path ID")
    payment_method: Optional[str] = Field(default=None, description="Payment method")
    payment_screenshot: Optional[str] = Field(default=None, max_length=500, description="Payment screenshot URL")
    coupon_code: Optional[str] = Field(default=None, max_length=50, description="Coupon code to apply")


class PathEnrollmentUpdate(LearningPathBase):
    """Schema for updating a path enrollment."""
    
    status: Optional[PathEnrollmentStatusEnum] = Field(default=None, description="Enrollment status")
    payment_verified: Optional[bool] = Field(default=None, description="Payment verified?")
    notes: Optional[str] = Field(default=None, max_length=500, description="Admin notes")


# ============================================================
# PATH PROGRESS UPDATE SCHEMA
# ============================================================

class PathProgressUpdate(LearningPathBase):
    """Schema for updating path progress."""
    
    path_enrollment_id: int = Field(..., gt=0, description="Path enrollment ID")
    course_id: int = Field(..., gt=0, description="Course ID to mark as completed")
    action: str = Field(..., description="Action: complete_course, uncomplete_course")


# ============================================================
# LEARNING PATH RESPONSE SCHEMA
# ============================================================

class PathCourseResponse(LearningPathBase):
    """Schema for path course response."""
    
    id: int = Field(..., description="Path course ID")
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    course_thumbnail: Optional[str] = Field(default=None, description="Course thumbnail")
    course_price: float = Field(..., description="Course price")
    
    order_index: int = Field(..., description="Order index")
    section: Optional[str] = Field(default=None, description="Section name")
    is_optional: bool = Field(..., description="Is optional")
    custom_description: Optional[str] = Field(default=None, description="Custom description")
    estimated_days: Optional[int] = Field(default=None, description="Estimated days")
    
    # NEW: Student-specific
    is_completed: bool = Field(default=False, description="Is completed by student")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class LearningPathResponse(LearningPathBase):
    """Schema for learning path response."""
    
    id: int = Field(..., description="Learning path ID")
    title: str = Field(..., description="Learning path title")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(default=None, description="Learning path description")
    short_description: Optional[str] = Field(default=None, description="Short description")
    
    thumbnail: Optional[str] = Field(default=None, description="Thumbnail URL")
    banner_image: Optional[str] = Field(default=None, description="Banner image URL")
    
    price: float = Field(..., description="Learning path price")
    original_price: Optional[float] = Field(default=None, description="Original price")
    currency: str = Field(..., description="Currency code")
    
    level: str = Field(..., description="Learning path level")
    display_level: str = Field(..., description="Human-readable level")
    category: Optional[str] = Field(default=None, description="Category")
    
    estimated_duration_hours: Optional[int] = Field(default=None, description="Estimated duration in hours")
    estimated_duration_weeks: Optional[int] = Field(default=None, description="Estimated duration in weeks")
    difficulty: int = Field(..., description="Difficulty score (1-10)")
    
    skills_covered: Optional[List[str]] = Field(default=None, description="Skills covered")
    learning_outcomes: Optional[List[str]] = Field(default=None, description="Learning outcomes")
    prerequisites: Optional[List[str]] = Field(default=None, description="Prerequisites")
    
    status: str = Field(..., description="Learning path status")
    display_status: str = Field(..., description="Human-readable status")
    is_featured: bool = Field(..., description="Featured on homepage")
    is_published: bool = Field(..., description="Is published")
    is_active: bool = Field(..., description="Is active")
    
    total_courses: int = Field(..., description="Total courses in path")
    total_students: int = Field(..., description="Total students enrolled")
    completion_rate: float = Field(..., description="Completion rate percentage")
    average_rating: float = Field(..., description="Average rating")
    total_reviews: int = Field(..., description="Total reviews")
    
    # NEW: Courses
    path_courses: List[PathCourseResponse] = Field(
        default_factory=list,
        description="Courses in the path"
    )
    
    # NEW: Creator
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# PATH ENROLLMENT RESPONSE SCHEMA
# ============================================================

class PathEnrollmentResponse(LearningPathBase):
    """Schema for path enrollment response."""
    
    id: int = Field(..., description="Path enrollment ID")
    path_id: int = Field(..., description="Learning path ID")
    path_title: str = Field(..., description="Learning path title")
    path_slug: str = Field(..., description="Learning path slug")
    path_thumbnail: Optional[str] = Field(default=None, description="Path thumbnail")
    
    student_id: int = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    student_email: str = Field(..., description="Student email")
    
    status: str = Field(..., description="Enrollment status")
    progress_percentage: int = Field(..., description="Progress percentage")
    completed_courses: int = Field(..., description="Completed courses count")
    total_courses: int = Field(..., description="Total courses count")
    
    is_fully_completed: bool = Field(..., description="Is fully completed")
    has_next_course: bool = Field(..., description="Has next course")
    next_course_id: Optional[int] = Field(default=None, description="Next course ID")
    current_course_id: Optional[int] = Field(default=None, description="Current course ID")
    
    # NEW: Completed course IDs
    completed_course_ids: Optional[List[int]] = Field(
        default=None,
        description="List of completed course IDs"
    )
    
    enrolled_at: datetime = Field(..., description="Enrollment timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last access timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# PATH DETAIL RESPONSE
# ============================================================

class PathDetailResponse(LearningPathResponse):
    """Schema for learning path detail response."""
    
    # NEW: Enrollment info for current user
    user_enrollment: Optional[PathEnrollmentResponse] = Field(
        default=None,
        description="Current user's enrollment"
    )
    user_is_enrolled: bool = Field(default=False, description="Current user is enrolled")
    user_progress: Optional[int] = Field(default=None, description="Current user's progress")
    
    # NEW: Reviews
    reviews: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Path reviews"
    )


# ============================================================
# LEARNING PATH LIST REQUEST (Filters)
# ============================================================

class LearningPathListRequest(LearningPathBase):
    """Schema for learning path list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title or description")
    status: Optional[LearningPathStatusEnum] = Field(default=None, description="Filter by status")
    level: Optional[LearningPathLevelEnum] = Field(default=None, description="Filter by level")
    category: Optional[str] = Field(default=None, description="Filter by category")
    is_featured: Optional[bool] = Field(default=None, description="Filter by featured")
    is_published: Optional[bool] = Field(default=None, description="Filter by published")
    price_min: Optional[float] = Field(default=None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(default=None, ge=0, description="Maximum price")
    created_by: Optional[int] = Field(default=None, description="Filter by creator")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# LEARNING PATH LIST RESPONSE
# ============================================================

class LearningPathListResponse(LearningPathBase):
    """Schema for paginated learning path list response."""
    
    paths: List[LearningPathResponse] = Field(..., description="List of learning paths")
    total: int = Field(..., description="Total learning paths")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# LEARNING PATH STATISTICS (Admin View)
# ============================================================

class LearningPathStatistics(LearningPathBase):
    """Schema for learning path statistics."""
    
    total_paths: int = Field(..., description="Total learning paths")
    draft: int = Field(..., description="Draft paths")
    published: int = Field(..., description="Published paths")
    archived: int = Field(..., description="Archived paths")
    featured: int = Field(..., description="Featured paths")
    
    # NEW: Enrollment stats
    total_enrollments: int = Field(..., description="Total path enrollments")
    active_enrollments: int = Field(..., description="Active enrollments")
    completed_enrollments: int = Field(..., description="Completed enrollments")
    
    # NEW: Revenue stats
    total_revenue: float = Field(..., description="Total revenue from paths")
    average_price: float = Field(..., description="Average path price")
    
    # NEW: Engagement stats
    average_completion_rate: float = Field(..., description="Average completion rate")
    most_popular_paths: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most popular learning paths"
    )
    
    # NEW: Level breakdown
    level_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Paths by level"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily enrollment trends"
    )


# ============================================================
# PATH REVIEW SCHEMAS
# ============================================================

class PathReviewCreate(LearningPathBase):
    """Schema for creating a learning path review."""
    
    path_id: int = Field(..., gt=0, description="Learning path ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Review title")
    content: Optional[str] = Field(default=None, min_length=10, max_length=5000, description="Review content")
    is_anonymous: bool = Field(default=False, description="Post anonymously")


class PathReviewResponse(LearningPathBase):
    """Schema for path review response."""
    
    id: int = Field(..., description="Review ID")
    path_id: int = Field(..., description="Learning path ID")
    student_id: int = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    is_anonymous: bool = Field(..., description="Is anonymous")
    
    rating: int = Field(..., description="Rating (1-5)")
    title: Optional[str] = Field(default=None, description="Review title")
    content: Optional[str] = Field(default=None, description="Review content")
    
    is_verified: bool = Field(..., description="Is verified")
    helpful_count: int = Field(..., description="Helpful votes count")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "LearningPathStatusEnum",
    "LearningPathLevelEnum",
    "PathEnrollmentStatusEnum",
    "LearningPathCreate",
    "LearningPathUpdate",
    "PathCourseCreate",
    "PathCourseUpdate",
    "PathEnrollmentCreate",
    "PathEnrollmentUpdate",
    "PathProgressUpdate",
    "PathCourseResponse",
    "LearningPathResponse",
    "PathEnrollmentResponse",
    "PathDetailResponse",
    "LearningPathListRequest",
    "LearningPathListResponse",
    "LearningPathStatistics",
    "PathReviewCreate",
    "PathReviewResponse",
]