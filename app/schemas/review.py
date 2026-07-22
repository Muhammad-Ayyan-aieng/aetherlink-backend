# ============================================================
# AETHER LINK - REVIEW SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# REVIEW ENUMS
# ============================================================

class ReviewStatusEnum(str, Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    HIDDEN = "hidden"
    DELETED = "deleted"


class ReviewTypeEnum(str, Enum):
    """Review type enumeration."""
    COURSE = "course"
    TEACHER = "teacher"
    INSTITUTION = "institution"


# ============================================================
# BASE SCHEMA
# ============================================================

class ReviewBase(BaseModel):
    """Base review schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# REVIEW CREATE SCHEMA
# ============================================================

class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    teacher_id: Optional[int] = Field(default=None, gt=0, description="Teacher ID (for teacher reviews)")
    
    rating: int = Field(..., ge=1, le=5, description="Overall rating (1-5)")
    
    # NEW: Breakdown ratings
    rating_teaching: Optional[int] = Field(default=None, ge=1, le=5, description="Teaching rating (1-5)")
    rating_content: Optional[int] = Field(default=None, ge=1, le=5, description="Content rating (1-5)")
    rating_support: Optional[int] = Field(default=None, ge=1, le=5, description="Support rating (1-5)")
    rating_value: Optional[int] = Field(default=None, ge=1, le=5, description="Value rating (1-5)")
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Review title")
    content: Optional[str] = Field(default=None, min_length=10, max_length=5000, description="Review content")
    
    # NEW: Pros and Cons
    pros: Optional[str] = Field(default=None, max_length=1000, description="Pros")
    cons: Optional[str] = Field(default=None, max_length=1000, description="Cons")
    
    would_recommend: bool = Field(default=True, description="Would recommend to others")
    
    # NEW: Anonymous review
    is_anonymous: bool = Field(default=False, description="Post anonymously")
    
    review_type: ReviewTypeEnum = Field(
        default=ReviewTypeEnum.COURSE,
        description="Review type"
    )
    
    @field_validator('rating_teaching', 'rating_content', 'rating_support', 'rating_value')
    @classmethod
    def validate_breakdown_ratings(cls, v: Optional[int]) -> Optional[int]:
        """Validate breakdown ratings are 1-5."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Breakdown ratings must be between 1 and 5')
        return v


# ============================================================
# REVIEW UPDATE SCHEMA
# ============================================================

class ReviewUpdate(ReviewBase):
    """Schema for updating a review."""
    
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Overall rating (1-5)")
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Review title")
    content: Optional[str] = Field(default=None, min_length=10, max_length=5000, description="Review content")
    pros: Optional[str] = Field(default=None, max_length=1000, description="Pros")
    cons: Optional[str] = Field(default=None, max_length=1000, description="Cons")
    would_recommend: Optional[bool] = Field(default=None, description="Would recommend")
    is_anonymous: Optional[bool] = Field(default=None, description="Post anonymously")


# ============================================================
# REVIEW MODERATION SCHEMA (Admin)
# ============================================================

class ReviewModerate(ReviewBase):
    """Schema for moderating a review."""
    
    status: ReviewStatusEnum = Field(..., description="New review status")
    notes: Optional[str] = Field(default=None, max_length=500, description="Moderation notes")
    rejection_reason: Optional[str] = Field(default=None, max_length=500, description="Rejection reason (if rejected)")


# ============================================================
# REVIEW RESPONSE SCHEMA
# ============================================================

class ReviewResponse(ReviewBase):
    """Schema for review response."""
    
    id: int = Field(..., description="Review ID")
    course_id: int = Field(..., description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    teacher_id: Optional[int] = Field(default=None, description="Teacher ID")
    teacher_name: Optional[str] = Field(default=None, description="Teacher name")
    
    student_id: int = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    is_anonymous: bool = Field(..., description="Is anonymous")
    display_name: str = Field(..., description="Display name (actual or anonymous)")
    
    rating: int = Field(..., description="Overall rating (1-5)")
    rating_display: str = Field(..., description="Star rating display")
    
    # NEW: Breakdown ratings
    rating_teaching: Optional[int] = Field(default=None, description="Teaching rating")
    rating_content: Optional[int] = Field(default=None, description="Content rating")
    rating_support: Optional[int] = Field(default=None, description="Support rating")
    rating_value: Optional[int] = Field(default=None, description="Value rating")
    breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Breakdown summary")
    
    title: Optional[str] = Field(default=None, description="Review title")
    content: Optional[str] = Field(default=None, description="Review content")
    pros: Optional[str] = Field(default=None, description="Pros")
    cons: Optional[str] = Field(default=None, description="Cons")
    
    would_recommend: bool = Field(..., description="Would recommend")
    is_verified: bool = Field(..., description="Is verified purchase")
    verification_method: Optional[str] = Field(default=None, description="Verification method")
    
    status: str = Field(..., description="Review status")
    display_status: str = Field(..., description="Human-readable status")
    
    helpful_count: int = Field(..., description="Helpful votes count")
    not_helpful_count: int = Field(..., description="Not helpful votes count")
    helpful_percentage: float = Field(..., description="Helpful percentage")
    
    # NEW: Response
    has_response: bool = Field(..., description="Has teacher/admin response")
    response: Optional[str] = Field(default=None, description="Response content")
    responded_at: Optional[datetime] = Field(default=None, description="Response timestamp")
    responded_by: Optional[int] = Field(default=None, description="Responded by user ID")
    responded_by_name: Optional[str] = Field(default=None, description="Responded by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# REVIEW DETAIL RESPONSE
# ============================================================

class ReviewDetailResponse(ReviewResponse):
    """Schema for review detail response."""
    
    # NEW: Helpful votes (list of users who voted)
    helpful_votes: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Helpful votes list"
    )
    
    # NEW: User's vote
    user_voted_helpful: Optional[bool] = Field(
        default=None,
        description="Current user voted helpful"
    )
    user_voted_not_helpful: Optional[bool] = Field(
        default=None,
        description="Current user voted not helpful"
    )


# ============================================================
# REVIEW HELPFUL VOTE SCHEMA
# ============================================================

class ReviewHelpfulVoteToggle(ReviewBase):
    """Schema for toggling a helpful vote."""
    
    review_id: int = Field(..., gt=0, description="Review ID")
    is_helpful: bool = Field(default=True, description="True for helpful, False for not helpful")


class ReviewHelpfulVoteResponse(ReviewBase):
    """Schema for helpful vote response."""
    
    voted: bool = Field(..., description="Vote recorded")
    is_helpful: bool = Field(..., description="Vote type")
    helpful_count: int = Field(..., description="Total helpful votes")
    not_helpful_count: int = Field(..., description="Total not helpful votes")
    helpful_percentage: float = Field(..., description="Helpful percentage")


# ============================================================
# REVIEW FLAG SCHEMA (Moderation)
# ============================================================

class ReviewFlagCreate(ReviewBase):
    """Schema for flagging a review."""
    
    review_id: int = Field(..., gt=0, description="Review ID")
    reason: str = Field(..., min_length=5, max_length=100, description="Flag reason")
    description: Optional[str] = Field(default=None, max_length=500, description="Detailed description")


class ReviewFlagResponse(ReviewBase):
    """Schema for review flag response."""
    
    id: int = Field(..., description="Flag ID")
    review_id: int = Field(..., description="Review ID")
    
    flagged_by: int = Field(..., description="Flagged by user ID")
    flagged_by_name: Optional[str] = Field(default=None, description="Flagged by user name")
    
    reason: str = Field(..., description="Flag reason")
    description: Optional[str] = Field(default=None, description="Detailed description")
    
    status: str = Field(..., description="Flag status")
    reviewed_by: Optional[int] = Field(default=None, description="Reviewed by user ID")
    reviewed_by_name: Optional[str] = Field(default=None, description="Reviewed by user name")
    reviewed_at: Optional[datetime] = Field(default=None, description="Review timestamp")
    review_notes: Optional[str] = Field(default=None, description="Review notes")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# REVIEW LIST REQUEST (Filters)
# ============================================================

class ReviewListRequest(ReviewBase):
    """Schema for review list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title or content")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Filter by rating")
    status: Optional[ReviewStatusEnum] = Field(default=None, description="Filter by status")
    review_type: Optional[ReviewTypeEnum] = Field(default=None, description="Filter by type")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    teacher_id: Optional[int] = Field(default=None, description="Filter by teacher")
    is_verified: Optional[bool] = Field(default=None, description="Filter by verified")
    would_recommend: Optional[bool] = Field(default=None, description="Filter by recommendation")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# REVIEW LIST RESPONSE
# ============================================================

class ReviewListResponse(ReviewBase):
    """Schema for paginated review list response."""
    
    reviews: List[ReviewResponse] = Field(..., description="List of reviews")
    total: int = Field(..., description="Total reviews")
    average_rating: float = Field(..., description="Average rating")
    rating_distribution: Dict[int, int] = Field(..., description="Rating distribution")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# REVIEW STATISTICS (Admin View)
# ============================================================

class ReviewStatistics(ReviewBase):
    """Schema for review statistics."""
    
    total_reviews: int = Field(..., description="Total reviews")
    pending: int = Field(..., description="Pending reviews")
    approved: int = Field(..., description="Approved reviews")
    rejected: int = Field(..., description="Rejected reviews")
    flagged: int = Field(..., description="Flagged reviews")
    hidden: int = Field(..., description="Hidden reviews")
    
    # NEW: Rating stats
    average_rating: float = Field(..., description="Average rating")
    rating_5_count: int = Field(..., description="5-star reviews")
    rating_4_count: int = Field(..., description="4-star reviews")
    rating_3_count: int = Field(..., description="3-star reviews")
    rating_2_count: int = Field(..., description="2-star reviews")
    rating_1_count: int = Field(..., description="1-star reviews")
    rating_distribution: Dict[int, int] = Field(..., description="Rating distribution")
    
    # NEW: Recommendation stats
    recommend_count: int = Field(..., description="Would recommend")
    not_recommend_count: int = Field(..., description="Would not recommend")
    recommend_rate: float = Field(..., description="Recommendation rate")
    
    # NEW: Verified vs unverified
    verified_reviews: int = Field(..., description="Verified reviews")
    unverified_reviews: int = Field(..., description="Unverified reviews")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Reviews by type"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily review trends"
    )
    
    # NEW: Top courses
    top_courses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Courses with highest ratings"
    )


# ============================================================
# REVIEW RESPONSE SCHEMA (Teacher/Admin)
# ============================================================

class ReviewResponseCreate(ReviewBase):
    """Schema for responding to a review."""
    
    review_id: int = Field(..., gt=0, description="Review ID")
    response: str = Field(..., min_length=1, max_length=2000, description="Response content")


class ReviewResponseUpdate(ReviewBase):
    """Schema for updating a review response."""
    
    review_id: int = Field(..., gt=0, description="Review ID")
    response: str = Field(..., min_length=1, max_length=2000, description="Response content")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ReviewStatusEnum",
    "ReviewTypeEnum",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewModerate",
    "ReviewResponse",
    "ReviewDetailResponse",
    "ReviewHelpfulVoteToggle",
    "ReviewHelpfulVoteResponse",
    "ReviewFlagCreate",
    "ReviewFlagResponse",
    "ReviewListRequest",
    "ReviewListResponse",
    "ReviewStatistics",
    "ReviewResponseCreate",
    "ReviewResponseUpdate",
]