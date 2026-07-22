# ============================================================
# AETHER LINK - CHAT SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# CHAT ENUMS
# ============================================================

class ConversationTypeEnum(str, Enum):
    """Conversation type enumeration."""
    DIRECT = "direct"          # 1-on-1 chat
    GROUP = "group"            # Group chat
    COURSE = "course"          # Course-specific chat
    SUPPORT = "support"        # Support ticket chat


class MessageTypeEnum(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"
    AUDIO = "audio"
    LINK = "link"
    SYSTEM = "system"
    TYPING = "typing"


class MessageStatusEnum(str, Enum):
    """Message status enumeration."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


class ParticipantRoleEnum(str, Enum):
    """Participant role in conversation."""
    MEMBER = "member"
    ADMIN = "admin"
    MODERATOR = "moderator"


# ============================================================
# BASE SCHEMA
# ============================================================

class ChatBase(BaseModel):
    """Base chat schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# CONVERSATION SCHEMAS
# ============================================================

class ConversationCreate(ChatBase):
    """Schema for creating a conversation."""
    
    conversation_type: ConversationTypeEnum = Field(
        default=ConversationTypeEnum.DIRECT,
        description="Conversation type"
    )
    
    title: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Conversation title (for groups)")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="Avatar URL (for groups)")
    course_id: Optional[int] = Field(default=None, gt=0, description="Course ID (for course chats)")
    
    # NEW: Participants
    participant_ids: List[int] = Field(..., min_length=1, description="List of participant user IDs")
    
    # NEW: Initial message
    initial_message: Optional[str] = Field(default=None, max_length=5000, description="Initial message")


class ConversationUpdate(ChatBase):
    """Schema for updating a conversation."""
    
    title: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Conversation title")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="Avatar URL")
    is_archived: Optional[bool] = Field(default=None, description="Archive/unarchive conversation")


class ConversationResponse(ChatBase):
    """Schema for conversation response."""
    
    id: int = Field(..., description="Conversation ID")
    title: Optional[str] = Field(default=None, description="Conversation title")
    avatar_url: Optional[str] = Field(default=None, description="Avatar URL")
    
    conversation_type: str = Field(..., description="Conversation type")
    is_direct: bool = Field(..., description="Is direct chat")
    is_group: bool = Field(..., description="Is group chat")
    is_course_chat: bool = Field(..., description="Is course chat")
    
    is_active: bool = Field(..., description="Is active")
    is_archived: bool = Field(..., description="Is archived")
    
    course_id: Optional[int] = Field(default=None, description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    
    created_by: int = Field(..., description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    participant_count: int = Field(..., description="Participant count")
    message_count: int = Field(..., description="Message count")
    
    last_message_at: Optional[datetime] = Field(default=None, description="Last message timestamp")
    last_message_preview: Optional[str] = Field(default=None, description="Last message preview")
    last_message_by: Optional[int] = Field(default=None, description="Last message sender ID")
    last_message_by_name: Optional[str] = Field(default=None, description="Last message sender name")
    
    # NEW: User-specific
    user_has_unread: bool = Field(default=False, description="Current user has unread messages")
    user_is_participant: bool = Field(default=False, description="Current user is participant")
    user_role: Optional[str] = Field(default=None, description="Current user's role")
    user_is_admin: bool = Field(default=False, description="Current user is admin")
    user_is_muted: bool = Field(default=False, description="Current user is muted")
    
    participants: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of participants"
    )
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CONVERSATION PARTICIPANT SCHEMAS
# ============================================================

class ParticipantAdd(ChatBase):
    """Schema for adding a participant to a conversation."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")
    user_id: int = Field(..., gt=0, description="User ID to add")
    role: ParticipantRoleEnum = Field(default=ParticipantRoleEnum.MEMBER, description="Participant role")


class ParticipantRemove(ChatBase):
    """Schema for removing a participant from a conversation."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")
    user_id: int = Field(..., gt=0, description="User ID to remove")


class ParticipantUpdate(ChatBase):
    """Schema for updating a participant's role."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")
    user_id: int = Field(..., gt=0, description="User ID")
    role: ParticipantRoleEnum = Field(..., description="New role")


class ParticipantResponse(ChatBase):
    """Schema for participant response."""
    
    id: int = Field(..., description="Participant ID")
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    user_email: str = Field(..., description="User email")
    user_avatar: Optional[str] = Field(default=None, description="User avatar")
    
    role: str = Field(..., description="Participant role")
    is_admin: bool = Field(..., description="Is admin")
    is_active: bool = Field(..., description="Is active")
    is_muted: bool = Field(..., description="Is muted")
    has_unread: bool = Field(..., description="Has unread messages")
    
    joined_at: datetime = Field(..., description="Joined at timestamp")
    last_read_at: Optional[datetime] = Field(default=None, description="Last read timestamp")


# ============================================================
# MESSAGE SCHEMAS
# ============================================================

class MessageCreate(ChatBase):
    """Schema for sending a message."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    
    message_type: MessageTypeEnum = Field(
        default=MessageTypeEnum.TEXT,
        description="Message type"
    )
    
    # NEW: Reply to message
    reply_to_id: Optional[int] = Field(default=None, gt=0, description="Reply to message ID")
    
    # NEW: Attachments
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments (url, type, name, size)"
    )
    
    # NEW: Rich content
    rich_content: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Rich content (for formatted messages)"
    )


class MessageUpdate(ChatBase):
    """Schema for updating a message."""
    
    content: str = Field(..., min_length=1, max_length=5000, description="New message content")


class MessageResponse(ChatBase):
    """Schema for message response."""
    
    id: int = Field(..., description="Message ID")
    conversation_id: int = Field(..., description="Conversation ID")
    
    sender_id: int = Field(..., description="Sender ID")
    sender_name: str = Field(..., description="Sender name")
    sender_avatar: Optional[str] = Field(default=None, description="Sender avatar")
    
    content: str = Field(..., description="Message content")
    message_type: str = Field(..., description="Message type")
    is_text: bool = Field(..., description="Is text message")
    is_image: bool = Field(..., description="Is image message")
    is_file: bool = Field(..., description="Is file message")
    is_system: bool = Field(..., description="Is system message")
    
    is_reply: bool = Field(..., description="Is reply")
    reply_to_id: Optional[int] = Field(default=None, description="Reply to message ID")
    reply_to_content: Optional[str] = Field(default=None, description="Reply to message content")
    reply_to_sender_name: Optional[str] = Field(default=None, description="Reply to sender name")
    
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    has_attachments: bool = Field(..., description="Has attachments")
    
    status: str = Field(..., description="Message status")
    display_status: str = Field(..., description="Human-readable status")
    
    is_sent: bool = Field(..., description="Is sent")
    is_delivered: bool = Field(..., description="Is delivered")
    is_read: bool = Field(..., description="Is read")
    is_edited: bool = Field(..., description="Is edited")
    is_deleted: bool = Field(..., description="Is deleted")
    
    read_by: Optional[List[int]] = Field(default=None, description="Read by user IDs")
    
    # NEW: Reactions
    reactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Reactions (emoji, user, user_name)"
    )
    has_reactions: bool = Field(..., description="Has reactions")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivered timestamp")
    read_at: Optional[datetime] = Field(default=None, description="Read timestamp")
    edited_at: Optional[datetime] = Field(default=None, description="Edit timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# MESSAGE REACTION SCHEMAS
# ============================================================

class MessageReactionAdd(ChatBase):
    """Schema for adding a reaction to a message."""
    
    message_id: int = Field(..., gt=0, description="Message ID")
    emoji: str = Field(..., min_length=1, max_length=20, description="Emoji to react with")


class MessageReactionRemove(ChatBase):
    """Schema for removing a reaction from a message."""
    
    message_id: int = Field(..., gt=0, description="Message ID")
    emoji: str = Field(..., min_length=1, max_length=20, description="Emoji to remove")


class MessageReactionResponse(ChatBase):
    """Schema for message reaction response."""
    
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    emoji: str = Field(..., description="Emoji")


# ============================================================
# MESSAGE READ RECEIPT SCHEMAS
# ============================================================

class MarkMessageRead(ChatBase):
    """Schema for marking messages as read."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")
    message_id: int = Field(..., gt=0, description="Message ID to mark as read")


class MarkAllMessagesRead(ChatBase):
    """Schema for marking all messages as read."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")


# ============================================================
# TYPING INDICATOR SCHEMAS
# ============================================================

class TypingIndicator(ChatBase):
    """Schema for typing indicator."""
    
    conversation_id: int = Field(..., gt=0, description="Conversation ID")
    is_typing: bool = Field(..., description="Is typing")


# ============================================================
# COURSE CHAT SCHEMAS
# ============================================================

class CourseChatRoomResponse(ChatBase):
    """Schema for course chat room response."""
    
    id: int = Field(..., description="Course chat room ID")
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    course_thumbnail: Optional[str] = Field(default=None, description="Course thumbnail")
    
    name: str = Field(..., description="Chat room name")
    description: Optional[str] = Field(default=None, description="Chat room description")
    is_active: bool = Field(..., description="Is active")
    
    message_count: int = Field(..., description="Message count")
    participant_count: int = Field(..., description="Participant count")
    last_message_at: Optional[datetime] = Field(default=None, description="Last message timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class CourseChatMessageCreate(ChatBase):
    """Schema for sending a course chat message."""
    
    room_id: int = Field(..., gt=0, description="Course chat room ID")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    
    message_type: MessageTypeEnum = Field(
        default=MessageTypeEnum.TEXT,
        description="Message type"
    )
    
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    
    # NEW: Mentions
    mentioned_users: Optional[List[int]] = Field(
        default=None,
        description="Mentioned user IDs"
    )


class CourseChatMessageResponse(ChatBase):
    """Schema for course chat message response."""
    
    id: int = Field(..., description="Message ID")
    room_id: int = Field(..., description="Course chat room ID")
    
    sender_id: int = Field(..., description="Sender ID")
    sender_name: str = Field(..., description="Sender name")
    sender_avatar: Optional[str] = Field(default=None, description="Sender avatar")
    
    content: str = Field(..., description="Message content")
    message_type: str = Field(..., description="Message type")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    mentioned_users: Optional[List[int]] = Field(
        default=None,
        description="Mentioned user IDs"
    )
    
    is_edited: bool = Field(..., description="Is edited")
    is_deleted: bool = Field(..., description="Is deleted")
    edited_at: Optional[datetime] = Field(default=None, description="Edit timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CHAT LIST REQUEST (Filters)
# ============================================================

class ChatListRequest(ChatBase):
    """Schema for chat list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    conversation_type: Optional[ConversationTypeEnum] = Field(
        default=None,
        description="Filter by conversation type"
    )
    is_archived: Optional[bool] = Field(default=None, description="Filter by archived")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    search: Optional[str] = Field(default=None, description="Search by title or participant name")
    sort_by: str = Field(default="last_message_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# CHAT STATISTICS
# ============================================================

class ChatStatistics(ChatBase):
    """Schema for chat statistics."""
    
    total_conversations: int = Field(..., description="Total conversations")
    direct_conversations: int = Field(..., description="Direct conversations")
    group_conversations: int = Field(..., description="Group conversations")
    course_conversations: int = Field(..., description="Course conversations")
    
    # NEW: Message stats
    total_messages: int = Field(..., description="Total messages")
    messages_today: int = Field(..., description="Messages today")
    messages_this_week: int = Field(..., description="Messages this week")
    messages_this_month: int = Field(..., description="Messages this month")
    
    # NEW: Participant stats
    total_participants: int = Field(..., description="Total participants")
    active_users_today: int = Field(..., description="Active users today")
    
    # NEW: Most active conversations
    most_active_conversations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most active conversations"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily messaging trends"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ConversationTypeEnum",
    "MessageTypeEnum",
    "MessageStatusEnum",
    "ParticipantRoleEnum",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ParticipantAdd",
    "ParticipantRemove",
    "ParticipantUpdate",
    "ParticipantResponse",
    "MessageCreate",
    "MessageUpdate",
    "MessageResponse",
    "MessageReactionAdd",
    "MessageReactionRemove",
    "MessageReactionResponse",
    "MarkMessageRead",
    "MarkAllMessagesRead",
    "TypingIndicator",
    "CourseChatRoomResponse",
    "CourseChatMessageCreate",
    "CourseChatMessageResponse",
    "ChatListRequest",
    "ChatStatistics",
]