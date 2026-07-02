# ============================================================
# AETHER LINK - COURSE SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


# ============================================================
# COURSE STATUS ENUM
# ============================================================

class CourseStatusEnum(str, Enum):
    """Course status enumeration for schemas."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ============================================================
# COURSE BASE SCHEMA
# ============================================================

class CourseBase(BaseModel):
    """Base course schema with common fields."""
    
    title: str = Field(..., min_length=3, max_length=255, description="Course title")
    slug: str = Field(..., min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=5000, description="Course description")
    price: float = Field(0, ge=0, le=999999, description="Course price (0-999,999 PKR)")
    thumbnail: Optional[str] = Field(None, max_length=500, description="Course thumbnail URL")
    status: CourseStatusEnum = Field(default=CourseStatusEnum.DRAFT, description="Course status")
    is_featured: bool = Field(default=False, description="Featured on homepage")
    
    # SEO Fields
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO description")
    meta_keywords: Optional[str] = Field(None, max_length=255, description="SEO keywords")
    
    @validator('slug')
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: lowercase, alphanumeric, hyphens only."""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()
    
    @validator('thumbnail')
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
    
    teacher_id: int = Field(..., gt=0, description="Teacher ID assigned to course")


# ============================================================
# COURSE UPDATE SCHEMA
# ============================================================

class CourseUpdate(BaseModel):
    """Schema for updating a course."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Course title")
    slug: Optional[str] = Field(None, min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=5000, description="Course description")
    price: Optional[float] = Field(None, ge=0, le=999999, description="Course price")
    thumbnail: Optional[str] = Field(None, max_length=500, description="Course thumbnail URL")
    status: Optional[CourseStatusEnum] = Field(None, description="Course status")
    is_featured: Optional[bool] = Field(None, description="Featured on homepage")
    
    # SEO Fields
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO description")
    meta_keywords: Optional[str] = Field(None, max_length=255, description="SEO keywords")
    
    @validator('slug')
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format."""
        if v is None:
            return v
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()
    
    @validator('thumbnail')
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
    teacher_id: int = Field(..., description="Teacher ID")
    teacher_name: Optional[str] = Field(None, description="Teacher's full name")
    total_sessions: int = Field(0, description="Total number of sessions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


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


# ============================================================
# COURSE DETAIL RESPONSE SCHEMA
# ============================================================

class CourseDetailResponse(CourseResponse):
    """Schema for course detail response with sessions."""
    
    sessions: List[SessionSummary] = Field(default=[], description="Course sessions")
    
    class Config:
        from_attributes = True


# ============================================================
# COURSE LIST RESPONSE
# ============================================================

class CourseListResponse(BaseModel):
    """Schema for paginated course list response."""
    
    courses: List[CourseResponse] = Field(..., description="List of courses")
    total: int = Field(..., description="Total number of courses")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CourseStatusEnum",
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "SessionSummary",
    "CourseDetailResponse",
    "CourseListResponse",
]