# ============================================================
# AETHER LINK - FORUM MODEL
# ============================================================
# Purpose: Course discussion forums with topics, replies, and likes
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, BigInteger, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class TopicStatus(str, enum.Enum):
    """Topic status enumeration."""
    ACTIVE = "active"
    LOCKED = "locked"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TopicType(str, enum.Enum):
    """Topic type enumeration."""
    GENERAL = "general"
    QUESTION = "question"
    ANNOUNCEMENT = "announcement"
    FEEDBACK = "feedback"
    RESOURCE = "resource"
    DISCUSSION = "discussion"


class ReplyStatus(str, enum.Enum):
    """Reply status enumeration."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    FLAGGED = "flagged"
    DELETED = "deleted"


# ============================================================
# 1. FORUM TOPIC MODEL
# ============================================================

class ForumTopic(Base):
    __tablename__ = "forum_topics"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # NEW: Short description (for listing)
    short_content = Column(String(200), nullable=True)
    
    # NEW: Topic type
    topic_type = Column(
        String(50),
        default=TopicType.GENERAL.value,
        nullable=False
    )
    
    # ============================================================
    # STATUS & FLAGS
    # ============================================================
    status = Column(
        String(20),
        default=TopicStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    is_locked = Column(Boolean, default=False, nullable=False, index=True)
    is_announcement = Column(Boolean, default=False, nullable=False, index=True)
    
    # ============================================================
    # STATISTICS (Cached)
    # ============================================================
    views_count = Column(Integer, default=0, nullable=False)
    replies_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    
    # NEW: Last activity tracking
    last_reply_at = Column(DateTime(timezone=True), nullable=True)
    last_reply_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # NEW: Solved tracking (for question type)
    is_solved = Column(Boolean, default=False, nullable=False)
    solved_by_reply_id = Column(Integer, ForeignKey("forum_replies.id", ondelete="SET NULL"), nullable=True)
    solved_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: MENTION TRACKING
    # ============================================================
    mentioned_users = Column(JSON, nullable=True)  # List of user IDs mentioned
    
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
        Index('ix_forum_topics_course_status', 'course_id', 'status'),
        Index('ix_forum_topics_pinned', 'is_pinned'),
        Index('ix_forum_topics_created_at', 'created_at'),
        Index('ix_forum_topics_last_reply', 'last_reply_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship(
        "Course",
        foreign_keys=[course_id]
    )
    
    created_by_user = relationship(
        "User",
        back_populates="forum_topics",
        foreign_keys=[created_by]
    )
    
    last_reply_by_user = relationship(
        "User",
        foreign_keys=[last_reply_by],
        uselist=False
    )
    
    replies = relationship(
        "ForumReply",
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="ForumReply.created_at"
    )
    
    # NEW: Solved by reply relationship
    solved_by_reply = relationship(
        "ForumReply",
        foreign_keys=[solved_by_reply_id],
        uselist=False
    )
    
    # NEW: Topic follows (for notification)
    followers = relationship(
        "ForumTopicFollow",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ForumTopic {self.id}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active(self) -> bool:
        """Check if topic is active."""
        return self.status == TopicStatus.ACTIVE.value
    
    @property
    def is_locked_topic(self) -> bool:
        """Check if topic is locked."""
        return self.status == TopicStatus.LOCKED.value or self.is_locked
    
    @property
    def is_archived_topic(self) -> bool:
        """Check if topic is archived."""
        return self.status == TopicStatus.ARCHIVED.value
    
    @property
    def is_deleted_topic(self) -> bool:
        """Check if topic is deleted."""
        return self.status == TopicStatus.DELETED.value
    
    @property
    def is_question(self) -> bool:
        """Check if topic is a question."""
        return self.topic_type == TopicType.QUESTION.value
    
    @property
    def is_announcement_topic(self) -> bool:
        """Check if topic is an announcement."""
        return self.is_announcement or self.topic_type == TopicType.ANNOUNCEMENT.value
    
    @property
    def display_type(self) -> str:
        """Get human-readable topic type."""
        type_map = {
            "general": "General",
            "question": "Question",
            "announcement": "Announcement",
            "feedback": "Feedback",
            "resource": "Resource",
            "discussion": "Discussion",
        }
        return type_map.get(self.topic_type, "General")
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_locked_topic:
            return "🔒 Locked"
        elif self.is_archived_topic:
            return "📦 Archived"
        elif self.is_deleted_topic:
            return "🗑️ Deleted"
        elif self.is_pinned:
            return "📌 Pinned"
        return "💬 Active"
    
    @property
    def is_hot(self) -> bool:
        """Check if topic is hot (high engagement)."""
        return self.replies_count >= 10 or self.views_count >= 100
    
    @property
    def age_days(self) -> int:
        """Get topic age in days."""
        if self.created_at is None:
            return 0
        delta = func.now() - self.created_at
        return delta.days
    
    @property
    def has_activity(self) -> bool:
        """Check if topic has recent activity."""
        if self.last_reply_at is None:
            return False
        delta = func.now() - self.last_reply_at
        return delta.days < 7
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def lock(self) -> None:
        """Lock the topic (no new replies)."""
        self.is_locked = True
        self.status = TopicStatus.LOCKED.value
    
    def unlock(self) -> None:
        """Unlock the topic."""
        self.is_locked = False
        self.status = TopicStatus.ACTIVE.value
    
    def pin(self) -> None:
        """Pin the topic."""
        self.is_pinned = True
        self.updated_at = func.now()
    
    def unpin(self) -> None:
        """Unpin the topic."""
        self.is_pinned = False
        self.updated_at = func.now()
    
    def archive(self) -> None:
        """Archive the topic."""
        self.status = TopicStatus.ARCHIVED.value
    
    def restore(self) -> None:
        """Restore an archived topic."""
        self.status = TopicStatus.ACTIVE.value
    
    def soft_delete(self) -> None:
        """Soft delete the topic."""
        self.status = TopicStatus.DELETED.value
        self.deleted_at = func.now()
    
    def mark_as_announcement(self) -> None:
        """Mark topic as announcement."""
        self.is_announcement = True
        self.topic_type = TopicType.ANNOUNCEMENT.value
    
    def mark_as_question(self) -> None:
        """Mark topic as question."""
        self.topic_type = TopicType.QUESTION.value
    
    def mark_solved(self, reply_id: int) -> None:
        """Mark question as solved."""
        self.is_solved = True
        self.solved_by_reply_id = reply_id
        self.solved_at = func.now()
    
    def mark_unsolved(self) -> None:
        """Mark question as unsolved."""
        self.is_solved = False
        self.solved_by_reply_id = None
        self.solved_at = None
    
    def increment_view(self) -> None:
        """Increment view count."""
        self.views_count += 1
    
    def increment_reply(self) -> None:
        """Increment reply count."""
        self.replies_count += 1
        self.last_reply_at = func.now()
    
    def decrement_reply(self) -> None:
        """Decrement reply count."""
        if self.replies_count > 0:
            self.replies_count -= 1
    
    def update_last_reply(self, user_id: int) -> None:
        """Update last reply information."""
        self.last_reply_at = func.now()
        self.last_reply_by = user_id
    
    def add_mention(self, user_id: int) -> None:
        """Add a mentioned user."""
        if self.mentioned_users is None:
            self.mentioned_users = []
        if user_id not in self.mentioned_users:
            self.mentioned_users.append(user_id)
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert topic to dictionary."""
        data = {
            "id": self.id,
            "course_id": self.course_id,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "title": self.title,
            "content": self.content,
            "short_content": self.short_content,
            "topic_type": self.topic_type,
            "display_type": self.display_type,
            "status": self.status,
            "display_status": self.display_status,
            "is_pinned": self.is_pinned,
            "is_locked": self.is_locked_topic,
            "is_announcement": self.is_announcement_topic,
            "is_solved": self.is_solved,
            "is_hot": self.is_hot,
            "views_count": self.views_count,
            "replies_count": self.replies_count,
            "likes_count": self.likes_count,
            "last_reply_at": self.last_reply_at.isoformat() if self.last_reply_at else None,
            "last_reply_by": self.last_reply_by,
            "last_reply_by_name": self.last_reply_by_user.full_name if self.last_reply_by_user else None,
            "has_activity": self.has_activity,
            "age_days": self.age_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "mentioned_users": self.mentioned_users,
                "solved_by_reply_id": self.solved_by_reply_id,
                "solved_at": self.solved_at.isoformat() if self.solved_at else None,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing topic data."""
        data = self.to_dict()
        data.pop("mentioned_users", None)
        data.pop("metadata", None)
        return data


# ============================================================
# 2. FORUM REPLY MODEL
# ============================================================

class ForumReply(Base):
    __tablename__ = "forum_replies"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    topic_id = Column(Integer, ForeignKey("forum_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # NEW: Parent reply (for nested threading)
    parent_reply_id = Column(Integer, ForeignKey("forum_replies.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # CONTENT
    # ============================================================
    content = Column(Text, nullable=False)
    
    # NEW: Short content (for preview)
    short_content = Column(String(200), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=ReplyStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    is_solution = Column(Boolean, default=False, nullable=False, index=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # LIKES
    # ============================================================
    likes_count = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # NEW: MENTION TRACKING
    # ============================================================
    mentioned_users = Column(JSON, nullable=True)  # List of user IDs mentioned
    
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
        Index('ix_forum_replies_topic', 'topic_id'),
        Index('ix_forum_replies_created_by', 'created_by'),
        Index('ix_forum_replies_status', 'status'),
        Index('ix_forum_replies_is_solution', 'is_solution'),
        Index('ix_forum_replies_parent', 'parent_reply_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    topic = relationship(
        "ForumTopic",
        back_populates="replies",
        foreign_keys=[topic_id]
    )
    
    created_by_user = relationship(
        "User",
        back_populates="forum_replies",
        foreign_keys=[created_by]
    )
    
    # NEW: Parent reply (for threading)
    parent_reply = relationship(
        "ForumReply",
        remote_side=[id],
        foreign_keys=[parent_reply_id],
        uselist=False
    )
    
    # NEW: Child replies
    child_replies = relationship(
        "ForumReply",
        foreign_keys=[parent_reply_id],
        cascade="all, delete-orphan"
    )
    
    likes = relationship(
        "ForumReplyLike",
        back_populates="reply",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ForumReply {self.id}: {self.created_by} -> {self.topic_id}>"
    
    def __str__(self) -> str:
        return f"Reply by {self.created_by_user.full_name if self.created_by_user else 'Unknown'}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active_reply(self) -> bool:
        """Check if reply is active."""
        return self.status == ReplyStatus.ACTIVE.value
    
    @property
    def is_hidden(self) -> bool:
        """Check if reply is hidden."""
        return self.status == ReplyStatus.HIDDEN.value
    
    @property
    def is_flagged(self) -> bool:
        """Check if reply is flagged."""
        return self.status == ReplyStatus.FLAGGED.value
    
    @property
    def is_deleted_reply(self) -> bool:
        """Check if reply is deleted."""
        return self.status == ReplyStatus.DELETED.value
    
    @property
    def is_solution_reply(self) -> bool:
        """Check if reply is marked as solution."""
        return self.is_solution
    
    @property
    def has_children(self) -> bool:
        """Check if reply has child replies."""
        return len(self.child_replies) > 0 if self.child_replies else False
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_solution:
            return "✅ Solution"
        elif self.is_deleted_reply:
            return "🗑️ Deleted"
        elif self.is_hidden:
            return "👻 Hidden"
        elif self.is_flagged:
            return "🚩 Flagged"
        return "💬 Active"
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def soft_delete_reply(self) -> None:
        """Soft delete the reply."""
        self.status = ReplyStatus.DELETED.value
        self.deleted_at = func.now()
        # Decrement topic reply count
        if self.topic:
            self.topic.decrement_reply()
    
    def restore_reply(self) -> None:
        """Restore a soft-deleted reply."""
        self.status = ReplyStatus.ACTIVE.value
        self.deleted_at = None
        # Increment topic reply count
        if self.topic:
            self.topic.increment_reply()
    
    def hide(self) -> None:
        """Hide the reply (moderator action)."""
        self.status = ReplyStatus.HIDDEN.value
    
    def unhide(self) -> None:
        """Unhide the reply."""
        self.status = ReplyStatus.ACTIVE.value
    
    def flag(self) -> None:
        """Flag the reply for moderation."""
        self.status = ReplyStatus.FLAGGED.value
    
    def mark_as_solution(self) -> None:
        """Mark reply as solution."""
        self.is_solution = True
        # Update topic
        if self.topic:
            self.topic.mark_solved(self.id)
    
    def unmark_as_solution(self) -> None:
        """Unmark reply as solution."""
        self.is_solution = False
        # Update topic
        if self.topic:
            self.topic.mark_unsolved()
    
    def edit(self, new_content: str) -> None:
        """Edit reply content."""
        self.content = new_content
        self.is_edited = True
        self.edited_at = func.now()
        self.updated_at = func.now()
    
    def add_mention(self, user_id: int) -> None:
        """Add a mentioned user."""
        if self.mentioned_users is None:
            self.mentioned_users = []
        if user_id not in self.mentioned_users:
            self.mentioned_users.append(user_id)
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert reply to dictionary."""
        data = {
            "id": self.id,
            "topic_id": self.topic_id,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "content": self.content,
            "short_content": self.short_content,
            "status": self.status,
            "display_status": self.display_status,
            "is_solution": self.is_solution,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "likes_count": self.likes_count,
            "parent_reply_id": self.parent_reply_id,
            "has_children": self.has_children,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "mentioned_users": self.mentioned_users,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing reply data."""
        data = self.to_dict()
        data.pop("mentioned_users", None)
        data.pop("metadata", None)
        return data


# ============================================================
# 3. FORUM REPLY LIKE MODEL
# ============================================================

class ForumReplyLike(Base):
    __tablename__ = "forum_reply_likes"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    reply_id = Column(Integer, ForeignKey("forum_replies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_forum_likes_unique', 'reply_id', 'user_id', unique=True),
        Index('ix_forum_likes_reply', 'reply_id'),
        Index('ix_forum_likes_user', 'user_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    reply = relationship(
        "ForumReply",
        back_populates="likes",
        foreign_keys=[reply_id]
    )
    
    user = relationship(
        "User",
        back_populates="forum_reply_likes",
        foreign_keys=[user_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ForumReplyLike {self.id}: {self.user_id} -> {self.reply_id}>"


# ============================================================
# 4. FORUM TOPIC FOLLOW (For notifications)
# ============================================================

class ForumTopicFollow(Base):
    """Track users following topics for notifications."""
    __tablename__ = "forum_topic_follows"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("forum_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Notification preferences
    notify_on_reply = Column(Boolean, default=True, nullable=False)
    notify_on_solution = Column(Boolean, default=True, nullable=False)
    notify_on_mention = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_forum_follows_unique', 'topic_id', 'user_id', unique=True),
        Index('ix_forum_follows_topic', 'topic_id'),
        Index('ix_forum_follows_user', 'user_id'),
    )
    
    # Relationships
    topic = relationship("ForumTopic", back_populates="followers")
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<ForumTopicFollow {self.id}: {self.user_id} -> {self.topic_id}>"


# ============================================================
# 5. FORUM FLAG (For moderation)
# ============================================================

class ForumFlag(Base):
    """Flag inappropriate content for moderation."""
    __tablename__ = "forum_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # NEW: Polymorphic flagging
    topic_id = Column(Integer, ForeignKey("forum_topics.id", ondelete="CASCADE"), nullable=True, index=True)
    reply_id = Column(Integer, ForeignKey("forum_replies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    flagged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    reason = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, reviewed, dismissed, actioned
    
    # Review tracking
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    flagger = relationship("User", foreign_keys=[flagged_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    topic = relationship("ForumTopic", foreign_keys=[topic_id])
    reply = relationship("ForumReply", foreign_keys=[reply_id])
    
    __table_args__ = (
        Index('ix_forum_flags_topic', 'topic_id'),
        Index('ix_forum_flags_reply', 'reply_id'),
        Index('ix_forum_flags_status', 'status'),
        Index('ix_forum_flags_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ForumFlag {self.id}: {self.reason}>"
    
    def review(self, reviewed_by: int, notes: str = None) -> None:
        """Mark flag as reviewed."""
        self.status = "reviewed"
        self.reviewed_by = reviewed_by
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes
    
    def dismiss(self, reviewed_by: int, notes: str = None) -> None:
        """Dismiss flag (no action needed)."""
        self.status = "dismissed"
        self.reviewed_by = reviewed_by
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes
    
    def action(self, reviewed_by: int, notes: str = None) -> None:
        """Action the flag (hide/delete content)."""
        self.status = "actioned"
        self.reviewed_by = reviewed_by
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes