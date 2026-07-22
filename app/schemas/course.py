# ============================================================
# AETHER LINK - COURSE SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


# ============================================================
# COURSE ENUMS (UPGRADED)
# ============================================================

class CourseStatusEnum(str, Enum):
    """Course status enumeration for schemas."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseLevelEnum(str, Enum):  # NEW
    """Course level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class CourseCategoryEnum(str, Enum):  # NEW
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


# ============================================================
# BASE SCHEMA
# ============================================================

class CourseBase(BaseModel):
    """Base course schema with common fields."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )
    
    title: str = Field(..., min_length=3, max_length=255, description="Course title")
    slug: str = Field(..., min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=10000, description="Course description")
    
    # NEW: Short description for listings
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description for listings")
    
    price: float = Field(default=0, ge=0, le=999999, description="Course price")
    thumbnail: Optional[str] = Field(default=None, max_length=500, description="Course thumbnail URL")
    
    # NEW: Level & Category
    level: Optional[CourseLevelEnum] = Field(default=None, description="Course level")
    category: Optional[CourseCategoryEnum] = Field(default=None, description="Course category")
    
    # NEW: Duration
    duration_weeks: int = Field(default=0, ge=0, description="Course duration in weeks")
    
    status: CourseStatusEnum = Field(default=CourseStatusEnum.DRAFT, description="Course status")
    is_featured: bool = Field(default=False, description="Featured on homepage")
    
    # NEW: Certificate settings
    certificate_enabled: bool = Field(default=True, description="Certificate available on completion")
    
    # SEO Fields
    meta_title: Optional[str] = Field(default=None, max_length=255, description="SEO title")
    meta_description: Optional[str] = Field(default=None, max_length=500, description="SEO description")
    meta_keywords: Optional[str] = Field(default=None, max_length=255, description="SEO keywords")
    
    # NEW: Prerequisites & Learning Objectives
    prerequisites: Optional[List[str]] = Field(default=None, description="Prerequisite skills or courses")
    learning_objectives: Optional[List[str]] = Field(default=None, description="Learning objectives")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: lowercase, alphanumeric, hyphens only."""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()
    
    @field_validator('thumbnail')
    @classmethod
    def validate_thumbnail(cls, v: Optional[str]) -> Optional[str]:
        """Validate thumbnail URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Thumbnail must be a valid URL')
        return v


# ============================================================
# COURSE CREATE SCHEMA
# ============================================================

class CourseCreate(CourseBase):
    """Schema for creating a course."""
    
    # NEW: Multiple teachers
    teacher_ids: Optional[List[int]] = Field(default=None, description="List of teacher IDs")
    
    # Legacy: Single teacher
    teacher_id: Optional[int] = Field(default=None, gt=0, description="Primary teacher ID")
    
    @field_validator('teacher_ids')
    @classmethod
    def validate_teacher_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Validate teacher IDs."""
        if v is None:
            return v
        if len(v) == 0:
            return None
        return list(set(v))  # Remove duplicates


# ============================================================
# COURSE UPDATE SCHEMA
# ============================================================

class CourseUpdate(BaseModel):
    """Schema for updating a course."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Course title")
    slug: Optional[str] = Field(default=None, min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=10000, description="Course description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description")
    price: Optional[float] = Field(default=None, ge=0, le=999999, description="Course price")
    thumbnail: Optional[str] = Field(default=None, max_length=500, description="Course thumbnail URL")
    
    # NEW: Level & Category
    level: Optional[CourseLevelEnum] = Field(default=None, description="Course level")
    category: Optional[CourseCategoryEnum] = Field(default=None, description="Course category")
    duration_weeks: Optional[int] = Field(default=None, ge=0, description="Course duration in weeks")
    
    status: Optional[CourseStatusEnum] = Field(default=None, description="Course status")
    is_featured: Optional[bool] = Field(default=None, description="Featured on homepage")
    certificate_enabled: Optional[bool] = Field(default=None, description="Certificate available")
    
    # SEO Fields
    meta_title: Optional[str] = Field(default=None, max_length=255, description="SEO title")
    meta_description: Optional[str] = Field(default=None, max_length=500, description="SEO description")
    meta_keywords: Optional[str] = Field(default=None, max_length=255, description="SEO keywords")
    
    # NEW: Prerequisites & Learning Objectives
    prerequisites: Optional[List[str]] = Field(default=None, description="Prerequisite skills or courses")
    learning_objectives: Optional[List[str]] = Field(default=None, description="Learning objectives")
    
    # NEW: Teacher updates
    teacher_ids: Optional[List[int]] = Field(default=None, description="List of teacher IDs")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format."""
        if v is None:
            return v
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()
    
    @field_validator('thumbnail')
    @classmethod
    def validate_thumbnail(cls, v: Optional[str]) -> Optional[str]:
        """Validate thumbnail URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Thumbnail must be a valid URL')
        return v


# ============================================================
# COURSE RESPONSE SCHEMA
# ============================================================

class CourseResponse(CourseBase):
    """Schema for course response."""
    
    id: int = Field(..., description="Course ID")
    teacher_id: int = Field(..., description="Primary teacher ID")
    teacher_name: Optional[str] = Field(default=None, description="Primary teacher's full name")
    
    # NEW: All teachers
    teachers: Optional[List[Dict[str, Any]]] = Field(default=None, description="All teachers assigned")
    
    total_sessions: int = Field(default=0, description="Total number of sessions")
    total_students_enrolled: int = Field(default=0, description="Total students enrolled")
    total_completed: int = Field(default=0, description="Total students completed")
    
    # NEW: Ratings
    average_rating: float = Field(default=0.0, description="Average rating")
    total_reviews: int = Field(default=0, description="Total reviews")
    
    # NEW: Publication info
    is_published: bool = Field(default=False, description="Is published")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    # NEW: Completion rate
    completion_rate: float = Field(default=0.0, description="Course completion rate")
    
    # NEW: Certificate template
    certificate_template_id: Optional[int] = Field(default=None, description="Certificate template ID")


# ============================================================
# SESSION SUMMARY SCHEMA
# ============================================================

class SessionSummary(BaseModel):
    """Schema for session summary in course detail."""
    
    id: int = Field(..., description="Session ID")
    session_number: int = Field(..., description="Session number")
    title: str = Field(..., description="Session title")
    date_time: datetime = Field(..., description="Session date and time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    status: str = Field(..., description="Session status")
    
    # NEW: Recording availability
    has_recording: bool = Field(default=False, description="Recording available")
    recording_url: Optional[str] = Field(default=None, description="Recording URL")


# ============================================================
# COURSE DETAIL RESPONSE SCHEMA
# ============================================================

class CourseDetailResponse(CourseResponse):
    """Schema for course detail response with sessions and materials."""
    
    sessions: List[SessionSummary] = Field(default=[], description="Course sessions")
    
    # NEW: Materials count
    materials_count: int = Field(default=0, description="Total materials")
    
    # NEW: Enrollment status for current user
    is_enrolled: bool = Field(default=False, description="Current user is enrolled")
    enrollment_status: Optional[str] = Field(default=None, description="Enrollment status")
    progress_percentage: Optional[int] = Field(default=None, description="User progress")


# ============================================================
# COURSE LIST REQUEST (Filters)
# ============================================================

class CourseListRequest(BaseModel):
    """Schema for course list request with filters."""
    model_config = ConfigDict(from_attributes=True)
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title or description")
    status: Optional[CourseStatusEnum] = Field(default=None, description="Filter by status")
    level: Optional[CourseLevelEnum] = Field(default=None, description="Filter by level")
    category: Optional[CourseCategoryEnum] = Field(default=None, description="Filter by category")
    is_featured: Optional[bool] = Field(default=None, description="Filter by featured")
    is_published: Optional[bool] = Field(default=None, description="Filter by published")
    price_min: Optional[float] = Field(default=None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(default=None, ge=0, description="Maximum price")
    teacher_id: Optional[int] = Field(default=None, description="Filter by teacher")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# COURSE LIST RESPONSE
# ============================================================

class CourseListResponse(BaseModel):
    """Schema for paginated course list response."""
    model_config = ConfigDict(from_attributes=True)
    
    courses: List[CourseResponse] = Field(..., description="List of courses")
    total: int = Field(..., description="Total number of courses")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# COURSE STATISTICS (Admin View)
# ============================================================

class CourseStatistics(BaseModel):
    """Schema for course statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_courses: int = Field(..., description="Total courses")
    published_courses: int = Field(..., description="Published courses")
    draft_courses: int = Field(..., description="Draft courses")
    archived_courses: int = Field(..., description="Archived courses")
    
    # NEW: Revenue stats
    total_revenue: float = Field(default=0.0, description="Total revenue")
    average_price: float = Field(default=0.0, description="Average course price")
    
    # NEW: Engagement stats
    total_enrollments: int = Field(default=0, description="Total enrollments")
    total_completions: int = Field(default=0, description="Total completions")
    overall_completion_rate: float = Field(default=0.0, description="Overall completion rate")
    
    # NEW: Popular courses
    popular_courses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most popular courses"
    )
    
    # NEW: Category breakdown
    category_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Courses by category"
    )


# ============================================================
# COURSE PUBLISH REQUEST
# ============================================================

class CoursePublishRequest(BaseModel):
    """Schema for publishing a course."""
    model_config = ConfigDict(from_attributes=True)
    
    publish: bool = Field(..., description="True to publish, False to unpublish")
    notify_students: bool = Field(default=True, description="Notify enrolled students")


# ============================================================
# COURSE TEACHER ASSIGNMENT
# ============================================================

class CourseTeacherAssignment(BaseModel):
    """Schema for assigning teachers to a course."""
    model_config = ConfigDict(from_attributes=True)
    
    teacher_ids: List[int] = Field(..., description="List of teacher IDs to assign")
    assign_by: int = Field(..., description="Admin ID assigning")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CourseStatusEnum",
    "CourseLevelEnum",
    "CourseCategoryEnum",
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "SessionSummary",
    "CourseDetailResponse",
    "CourseListRequest",
    "CourseListResponse",
    "CourseStatistics",
    "CoursePublishRequest",
    "CourseTeacherAssignment",
]