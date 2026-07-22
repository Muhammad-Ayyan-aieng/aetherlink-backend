# ============================================================
# AETHER LINK - FORUM SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# FORUM ENUMS
# ============================================================

class TopicStatusEnum(str, Enum):
    """Topic status enumeration."""
    ACTIVE = "active"
    LOCKED = "locked"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TopicTypeEnum(str, Enum):
    """Topic type enumeration."""
    GENERAL = "general"
    QUESTION = "question"
    ANNOUNCEMENT = "announcement"
    FEEDBACK = "feedback"
    RESOURCE = "resource"
    DISCUSSION = "discussion"


class ReplyStatusEnum(str, Enum):
    """Reply status enumeration."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    FLAGGED = "flagged"
    DELETED = "deleted"


# ============================================================
# BASE SCHEMA
# ============================================================

class ForumBase(BaseModel):
    """Base forum schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# FORUM TOPIC SCHEMAS
# ============================================================

class ForumTopicCreate(ForumBase):
    """Schema for creating a forum topic."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    title: str = Field(..., min_length=3, max_length=255, description="Topic title")
    content: str = Field(..., min_length=10, description="Topic content")
    
    topic_type: TopicTypeEnum = Field(
        default=TopicTypeEnum.GENERAL,
        description="Topic type"
    )
    
    # NEW: Mentions
    mentioned_users: Optional[List[int]] = Field(
        default=None,
        description="User IDs mentioned in the topic"
    )


class ForumTopicUpdate(ForumBase):
    """Schema for updating a forum topic."""
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Topic title")
    content: Optional[str] = Field(default=None, min_length=10, description="Topic content")
    topic_type: Optional[TopicTypeEnum] = Field(default=None, description="Topic type")
    
    # NEW: Moderation actions
    pin: Optional[bool] = Field(default=None, description="Pin/unpin topic")
    lock: Optional[bool] = Field(default=None, description="Lock/unlock topic")
    archive: Optional[bool] = Field(default=None, description="Archive/unarchive topic")
    
    # NEW: Mark as solution (for question type)
    solution_reply_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Reply ID to mark as solution (null to unsolve)"
    )


class ForumTopicResponse(ForumBase):
    """Schema for forum topic response."""
    
    id: int = Field(..., description="Topic ID")
    course_id: int = Field(..., description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    
    created_by: int = Field(..., description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    created_by_avatar: Optional[str] = Field(default=None, description="Created by user avatar")
    
    title: str = Field(..., description="Topic title")
    content: str = Field(..., description="Topic content")
    
    topic_type: str = Field(..., description="Topic type")
    display_type: str = Field(..., description="Human-readable type")
    
    status: str = Field(..., description="Topic status")
    display_status: str = Field(..., description="Human-readable status")
    
    is_pinned: bool = Field(..., description="Is pinned")
    is_locked: bool = Field(..., description="Is locked")
    is_announcement: bool = Field(..., description="Is announcement")
    is_solved: bool = Field(..., description="Is solved (for question type)")
    
    views_count: int = Field(..., description="View count")
    replies_count: int = Field(..., description="Reply count")
    likes_count: int = Field(..., description="Like count")
    
    is_hot: bool = Field(..., description="Is hot topic")
    has_activity: bool = Field(..., description="Has recent activity")
    age_days: int = Field(..., description="Age in days")
    
    last_reply_at: Optional[datetime] = Field(default=None, description="Last reply timestamp")
    last_reply_by: Optional[int] = Field(default=None, description="Last reply by user ID")
    last_reply_by_name: Optional[str] = Field(default=None, description="Last reply by user name")
    
    solved_by_reply_id: Optional[int] = Field(default=None, description="Solution reply ID")
    solved_at: Optional[datetime] = Field(default=None, description="Solution timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# FORUM REPLY SCHEMAS
# ============================================================

class ForumReplyCreate(ForumBase):
    """Schema for creating a forum reply."""
    
    topic_id: int = Field(..., gt=0, description="Topic ID")
    content: str = Field(..., min_length=1, description="Reply content")
    
    # NEW: Parent reply (for threading)
    parent_reply_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Parent reply ID (for threading)"
    )
    
    # NEW: Mentions
    mentioned_users: Optional[List[int]] = Field(
        default=None,
        description="User IDs mentioned in the reply"
    )


class ForumReplyUpdate(ForumBase):
    """Schema for updating a forum reply."""
    
    content: Optional[str] = Field(default=None, min_length=1, description="Reply content")
    
    # NEW: Moderation actions
    hide: Optional[bool] = Field(default=None, description="Hide/unhide reply")
    flag: Optional[bool] = Field(default=None, description="Flag/unflag reply")
    mark_solution: Optional[bool] = Field(default=None, description="Mark as solution")


class ForumReplyResponse(ForumBase):
    """Schema for forum reply response."""
    
    id: int = Field(..., description="Reply ID")
    topic_id: int = Field(..., description="Topic ID")
    
    created_by: int = Field(..., description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    created_by_avatar: Optional[str] = Field(default=None, description="Created by user avatar")
    
    content: str = Field(..., description="Reply content")
    
    status: str = Field(..., description="Reply status")
    display_status: str = Field(..., description="Human-readable status")
    
    is_solution: bool = Field(..., description="Is marked as solution")
    is_edited: bool = Field(..., description="Is edited")
    edited_at: Optional[datetime] = Field(default=None, description="Edit timestamp")
    
    likes_count: int = Field(..., description="Like count")
    has_children: bool = Field(..., description="Has child replies")
    parent_reply_id: Optional[int] = Field(default=None, description="Parent reply ID")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# FORUM REPLY LIKE SCHEMA
# ============================================================

class ForumReplyLikeToggle(ForumBase):
    """Schema for toggling a reply like."""
    
    reply_id: int = Field(..., gt=0, description="Reply ID")


class ForumReplyLikeResponse(ForumBase):
    """Schema for reply like response."""
    
    liked: bool = Field(..., description="Is liked")
    likes_count: int = Field(..., description="Total likes count")


# ============================================================
# FORUM TOPIC FOLLOW SCHEMAS
# ============================================================

class ForumTopicFollowToggle(ForumBase):
    """Schema for toggling topic follow."""
    
    topic_id: int = Field(..., gt=0, description="Topic ID")


class ForumTopicFollowResponse(ForumBase):
    """Schema for topic follow response."""
    
    following: bool = Field(..., description="Is following")
    followers_count: int = Field(..., description="Total followers count")


# ============================================================
# FORUM FLAG SCHEMA (Moderation)
# ============================================================

class ForumFlagCreate(ForumBase):
    """Schema for flagging forum content."""
    
    topic_id: Optional[int] = Field(default=None, gt=0, description="Topic ID to flag")
    reply_id: Optional[int] = Field(default=None, gt=0, description="Reply ID to flag")
    reason: str = Field(..., min_length=5, max_length=100, description="Flag reason")
    description: Optional[str] = Field(default=None, max_length=500, description="Detailed description")
    
    @field_validator('topic_id', 'reply_id')
    @classmethod
    def validate_target(cls, v: Optional[int], info: Dict[str, Any]) -> Optional[int]:
        """Validate at least one target is provided."""
        data = info.data
        if not data.get('topic_id') and not data.get('reply_id'):
            raise ValueError('Either topic_id or reply_id must be provided')
        return v


class ForumFlagResponse(ForumBase):
    """Schema for flag response."""
    
    id: int = Field(..., description="Flag ID")
    topic_id: Optional[int] = Field(default=None, description="Topic ID")
    reply_id: Optional[int] = Field(default=None, description="Reply ID")
    
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
# FORUM DETAIL RESPONSE
# ============================================================

class ForumTopicDetailResponse(ForumTopicResponse):
    """Schema for forum topic detail response with replies."""
    
    replies: Optional[List[ForumReplyResponse]] = Field(
        default=None,
        description="Replies in the topic"
    )
    
    # NEW: User-specific info
    user_following: bool = Field(default=False, description="User is following this topic")
    user_has_replied: bool = Field(default=False, description="User has replied to this topic")
    user_can_reply: bool = Field(default=True, description="User can reply to this topic")


# ============================================================
# FORUM LIST REQUEST (Filters)
# ============================================================

class ForumTopicListRequest(ForumBase):
    """Schema for forum topic list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title or content")
    topic_type: Optional[TopicTypeEnum] = Field(default=None, description="Filter by type")
    status: Optional[TopicStatusEnum] = Field(default=None, description="Filter by status")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    created_by: Optional[int] = Field(default=None, description="Filter by creator")
    is_pinned: Optional[bool] = Field(default=None, description="Filter by pinned")
    is_solved: Optional[bool] = Field(default=None, description="Filter by solved")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# FORUM TOPIC LIST RESPONSE
# ============================================================

class ForumTopicListResponse(ForumBase):
    """Schema for paginated forum topic list response."""
    
    topics: List[ForumTopicResponse] = Field(..., description="List of topics")
    total: int = Field(..., description="Total topics")
    pinned_count: int = Field(..., description="Pinned topics count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# FORUM REPLY LIST RESPONSE
# ============================================================

class ForumReplyListResponse(ForumBase):
    """Schema for paginated forum reply list response."""
    
    replies: List[ForumReplyResponse] = Field(..., description="List of replies")
    total: int = Field(..., description="Total replies")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# FORUM STATISTICS
# ============================================================

class ForumStatistics(ForumBase):
    """Schema for forum statistics."""
    
    total_topics: int = Field(..., description="Total topics")
    total_replies: int = Field(..., description="Total replies")
    total_likes: int = Field(..., description="Total likes")
    total_views: int = Field(..., description="Total views")
    
    # NEW: Topic breakdown
    active_topics: int = Field(..., description="Active topics")
    locked_topics: int = Field(..., description="Locked topics")
    archived_topics: int = Field(..., description="Archived topics")
    pinned_topics: int = Field(..., description="Pinned topics")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Topics by type"
    )
    
    # NEW: Engagement
    average_replies_per_topic: float = Field(..., description="Average replies per topic")
    most_active_topic: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Most active topic"
    )
    most_active_user: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Most active user"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily forum activity trends"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "TopicStatusEnum",
    "TopicTypeEnum",
    "ReplyStatusEnum",
    "ForumTopicCreate",
    "ForumTopicUpdate",
    "ForumTopicResponse",
    "ForumReplyCreate",
    "ForumReplyUpdate",
    "ForumReplyResponse",
    "ForumReplyLikeToggle",
    "ForumReplyLikeResponse",
    "ForumTopicFollowToggle",
    "ForumTopicFollowResponse",
    "ForumFlagCreate",
    "ForumFlagResponse",
    "ForumTopicDetailResponse",
    "ForumTopicListRequest",
    "ForumTopicListResponse",
    "ForumReplyListResponse",
    "ForumStatistics",
]