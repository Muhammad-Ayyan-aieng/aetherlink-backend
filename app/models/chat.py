# ============================================================
# AETHER LINK - CHAT MODEL
# ============================================================
# Purpose: Real-time chat system for student-teacher communication
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class ConversationType(str, enum.Enum):
    """Conversation type enumeration."""
    DIRECT = "direct"          # 1-on-1 chat
    GROUP = "group"            # Group chat
    COURSE = "course"          # Course-specific chat
    SUPPORT = "support"        # Support ticket chat


class MessageType(str, enum.Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"
    AUDIO = "audio"
    LINK = "link"
    SYSTEM = "system"
    TYPING = "typing"


class MessageStatus(str, enum.Enum):
    """Message status enumeration."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


class ParticipantRole(str, enum.Enum):
    """Participant role in conversation."""
    MEMBER = "member"
    ADMIN = "admin"
    MODERATOR = "moderator"


# ============================================================
# 1. CONVERSATION MODEL
# ============================================================

class Conversation(Base):
    __tablename__ = "conversations"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=True)  # For group chats
    avatar_url = Column(String(500), nullable=True)  # For group chats
    
    # ============================================================
    # CONVERSATION TYPE
    # ============================================================
    conversation_type = Column(
        String(50),
        default=ConversationType.DIRECT.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # COURSE RELATIONSHIP (For course chats)
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # ============================================================
    # CREATOR
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    # ============================================================
    # LAST ACTIVITY
    # ============================================================
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_preview = Column(String(255), nullable=True)
    last_message_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # STATISTICS
    # ============================================================
    message_count = Column(Integer, default=0, nullable=False)
    participant_count = Column(Integer, default=0, nullable=False)
    
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
        Index('ix_conversations_type', 'conversation_type'),
        Index('ix_conversations_course', 'course_id'),
        Index('ix_conversations_created_by', 'created_by'),
        Index('ix_conversations_last_message', 'last_message_at'),
        Index('ix_conversations_active', 'is_active'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    created_by_user = relationship(
        "User",
        back_populates="conversations_created",
        foreign_keys=[created_by]
    )
    
    course = relationship(
        "Course",
        foreign_keys=[course_id]
    )
    
    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Conversation {self.id}: {self.title or 'Direct Chat'}>"
    
    def __str__(self) -> str:
        return self.title or f"Conversation {self.id}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_direct(self) -> bool:
        """Check if conversation is direct (1-on-1)."""
        return self.conversation_type == ConversationType.DIRECT.value
    
    @property
    def is_group(self) -> bool:
        """Check if conversation is group chat."""
        return self.conversation_type == ConversationType.GROUP.value
    
    @property
    def is_course_chat(self) -> bool:
        """Check if conversation is course-specific."""
        return self.conversation_type == ConversationType.COURSE.value
    
    @property
    def is_support_chat(self) -> bool:
        """Check if conversation is support ticket."""
        return self.conversation_type == ConversationType.SUPPORT.value
    
    @property
    def has_unread_messages(self) -> bool:
        """Check if there are unread messages."""
        # This would need participant-specific logic
        return False  # Placeholder
    
    @property
    def display_name(self) -> str:
        """Get display name for conversation."""
        if self.title:
            return self.title
        if self.is_direct:
            # Get other participant's name
            # This would need to be resolved in service
            return "Direct Chat"
        return f"Conversation {self.id}"
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def add_participant(self, user_id: int, role: str = "member") -> None:
        """Add a participant to the conversation."""
        from sqlalchemy.orm import Session
        
        # Check if already participant
        existing = [p for p in self.participants if p.user_id == user_id]
        if existing:
            return
        
        participant = ConversationParticipant(
            user_id=user_id,
            role=role
        )
        self.participants.append(participant)
        self.participant_count += 1
    
    def remove_participant(self, user_id: int) -> None:
        """Remove a participant from the conversation."""
        self.participants = [p for p in self.participants if p.user_id != user_id]
        self.participant_count = len(self.participants)
    
    def update_last_message(self, message: 'Message') -> None:
        """Update last message info."""
        self.last_message_at = message.created_at
        self.last_message_preview = message.content[:255] if message.content else ""
        self.last_message_by = message.sender_id
        self.message_count += 1
    
    def archive_conversation(self) -> None:
        """Archive the conversation."""
        self.is_archived = True
    
    def unarchive_conversation(self) -> None:
        """Unarchive the conversation."""
        self.is_archived = False
    
    def soft_delete_conversation(self) -> None:
        """Soft delete the conversation."""
        self.deleted_at = func.now()
        self.is_active = False
    
    def restore_conversation(self) -> None:
        """Restore a soft-deleted conversation."""
        self.deleted_at = None
        self.is_active = True
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert conversation to dictionary."""
        data = {
            "id": self.id,
            "title": self.title,
            "avatar_url": self.avatar_url,
            "conversation_type": self.conversation_type,
            "is_direct": self.is_direct,
            "is_group": self.is_group,
            "is_course_chat": self.is_course_chat,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "course_id": self.course_id,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "participant_count": self.participant_count,
            "message_count": self.message_count,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "last_message_preview": self.last_message_preview,
            "last_message_by": self.last_message_by,
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
        """Public-facing conversation data."""
        data = self.to_dict()
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing conversation data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. CONVERSATION PARTICIPANT MODEL
# ============================================================

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # ROLE
    # ============================================================
    role = Column(
        String(20),
        default=ParticipantRole.MEMBER.value,
        nullable=False
    )
    
    # ============================================================
    # READ RECEIPT
    # ============================================================
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    last_read_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    is_active = Column(Boolean, default=True, nullable=False)
    is_muted = Column(Boolean, default=False, nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_conversation_participants_unique', 'conversation_id', 'user_id', unique=True),
        Index('ix_conversation_participants_conversation', 'conversation_id'),
        Index('ix_conversation_participants_user', 'user_id'),
        Index('ix_conversation_participants_active', 'is_active'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    conversation = relationship(
        "Conversation",
        back_populates="participants",
        foreign_keys=[conversation_id]
    )
    
    user = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    last_read_message = relationship(
        "Message",
        foreign_keys=[last_read_message_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ConversationParticipant {self.id}: {self.user_id} -> {self.conversation_id}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_admin(self) -> bool:
        """Check if participant is admin."""
        return self.role == ParticipantRole.ADMIN.value
    
    @property
    def is_moderator(self) -> bool:
        """Check if participant is moderator."""
        return self.role == ParticipantRole.MODERATOR.value
    
    @property
    def is_member(self) -> bool:
        """Check if participant is member."""
        return self.role == ParticipantRole.MEMBER.value
    
    @property
    def has_unread(self) -> bool:
        """Check if there are unread messages."""
        if self.last_read_at is None:
            return True
        if self.conversation and self.conversation.last_message_at:
            return self.conversation.last_message_at > self.last_read_at
        return False
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def mark_read(self, message_id: int) -> None:
        """Mark messages as read up to a specific message."""
        self.last_read_at = func.now()
        self.last_read_message_id = message_id
    
    def mute(self) -> None:
        """Mute conversation for this user."""
        self.is_muted = True
    
    def unmute(self) -> None:
        """Unmute conversation for this user."""
        self.is_muted = False
    
    def leave(self) -> None:
        """Leave the conversation."""
        self.is_active = False
        self.left_at = func.now()
    
    def join(self) -> None:
        """Join the conversation."""
        self.is_active = True
        self.left_at = None
    
    def set_role(self, role: str) -> None:
        """Set participant role."""
        if role in [r.value for r in ParticipantRole]:
            self.role = role
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self) -> dict:
        """Convert participant to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "role": self.role,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "is_muted": self.is_muted,
            "has_unread": self.has_unread,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
        }


# ============================================================
# 3. MESSAGE MODEL
# ============================================================

class Message(Base):
    __tablename__ = "messages"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # NEW: Reply to specific message
    reply_to_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # CONTENT
    # ============================================================
    content = Column(Text, nullable=False)
    
    # NEW: Message type
    message_type = Column(
        String(50),
        default=MessageType.TEXT.value,
        nullable=False
    )
    
    # NEW: Rich content
    rich_content = Column(JSON, nullable=True)  # For formatted messages
    
    # ============================================================
    # ATTACHMENTS
    # ============================================================
    attachments = Column(JSON, nullable=True)
    # Example: [{"url": "https://...", "type": "image", "name": "file.jpg", "size": 1024}]
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=MessageStatus.SENT.value,
        nullable=False,
        index=True
    )
    
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # DELIVERY INFO
    # ============================================================
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    read_by = Column(JSON, nullable=True)  # List of user IDs who read the message
    
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
        Index('ix_messages_conversation', 'conversation_id'),
        Index('ix_messages_sender', 'sender_id'),
        Index('ix_messages_status', 'status'),
        Index('ix_messages_created_at', 'created_at'),
        Index('ix_messages_type', 'message_type'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    conversation = relationship(
        "Conversation",
        back_populates="messages",
        foreign_keys=[conversation_id]
    )
    
    sender = relationship(
        "User",
        back_populates="messages_sent",
        foreign_keys=[sender_id]
    )
    
    reply_to = relationship(
        "Message",
        remote_side=[id],
        foreign_keys=[reply_to_id],
        uselist=False
    )
    
    reactions = relationship(
        "MessageReaction",
        back_populates="message",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Message {self.id}: {self.content[:50]}...>"
    
    def __str__(self) -> str:
        return self.content[:50] + "..." if len(self.content) > 50 else self.content
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_text(self) -> bool:
        """Check if message is text."""
        return self.message_type == MessageType.TEXT.value
    
    @property
    def is_image(self) -> bool:
        """Check if message is image."""
        return self.message_type == MessageType.IMAGE.value
    
    @property
    def is_file(self) -> bool:
        """Check if message is file."""
        return self.message_type == MessageType.FILE.value
    
    @property
    def is_system_message(self) -> bool:
        """Check if message is system message."""
        return self.message_type == MessageType.SYSTEM.value
    
    @property
    def is_sent(self) -> bool:
        """Check if message is sent."""
        return self.status == MessageStatus.SENT.value
    
    @property
    def is_delivered(self) -> bool:
        """Check if message is delivered."""
        return self.status == MessageStatus.DELIVERED.value
    
    @property
    def is_read_message(self) -> bool:
        """Check if message is read."""
        return self.status == MessageStatus.READ.value
    
    @property
    def is_failed(self) -> bool:
        """Check if message failed."""
        return self.status == MessageStatus.FAILED.value
    
    @property
    def has_attachments(self) -> bool:
        """Check if message has attachments."""
        return self.attachments is not None and len(self.attachments) > 0
    
    @property
    def has_reactions(self) -> bool:
        """Check if message has reactions."""
        return len(self.reactions) > 0 if self.reactions else False
    
    @property
    def is_reply(self) -> bool:
        """Check if message is a reply."""
        return self.reply_to_id is not None
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "sent": "📤 Sent",
            "delivered": "📬 Delivered",
            "read": "👁️ Read",
            "failed": "❌ Failed",
            "deleted": "🗑️ Deleted",
        }
        return status_map.get(self.status, "Unknown")
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def mark_delivered(self) -> None:
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED.value
        self.delivered_at = func.now()
    
    def mark_read(self, user_id: int) -> None:
        """Mark message as read by a user."""
        if self.read_by is None:
            self.read_by = []
        if user_id not in self.read_by:
            self.read_by.append(user_id)
        
        # Update status to READ if not already
        if self.status != MessageStatus.READ.value:
            self.status = MessageStatus.READ.value
            self.read_at = func.now()
    
    def mark_failed(self) -> None:
        """Mark message as failed."""
        self.status = MessageStatus.FAILED.value
    
    def edit_content(self, new_content: str) -> None:
        """Edit message content."""
        self.content = new_content
        self.is_edited = True
        self.edited_at = func.now()
    
    def soft_delete_message(self) -> None:
        """Soft delete the message."""
        self.is_deleted = True
        self.deleted_at = func.now()
    
    def restore_message(self) -> None:
        """Restore a soft-deleted message."""
        self.is_deleted = False
        self.deleted_at = None
    
    def add_reaction(self, user_id: int, emoji: str) -> None:
        """Add a reaction to the message."""
        # Check if reaction already exists
        existing = [r for r in self.reactions if r.user_id == user_id and r.emoji == emoji]
        if existing:
            return
        
        reaction = MessageReaction(
            user_id=user_id,
            emoji=emoji
        )
        self.reactions.append(reaction)
    
    def remove_reaction(self, user_id: int, emoji: str) -> None:
        """Remove a reaction from the message."""
        self.reactions = [
            r for r in self.reactions 
            if not (r.user_id == user_id and r.emoji == emoji)
        ]
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert message to dictionary."""
        data = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "sender_avatar": self.sender.profile_picture if self.sender else None,
            "content": self.content,
            "message_type": self.message_type,
            "is_text": self.is_text,
            "is_image": self.is_image,
            "is_file": self.is_file,
            "is_system": self.is_system_message,
            "is_reply": self.is_reply,
            "reply_to_id": self.reply_to_id,
            "attachments": self.attachments,
            "has_attachments": self.has_attachments,
            "status": self.status,
            "display_status": self.display_status,
            "is_sent": self.is_sent,
            "is_delivered": self.is_delivered,
            "is_read": self.is_read_message,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "read_by": self.read_by,
            "reactions": [
                {
                    "user_id": r.user_id,
                    "user_name": r.user.full_name if r.user else None,
                    "emoji": r.emoji,
                }
                for r in self.reactions
            ] if self.reactions else [],
        }
        
        if include_sensitive:
            data.update({
                "rich_content": self.rich_content,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing message data."""
        data = self.to_dict()
        data.pop("read_by", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing message data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 4. MESSAGE REACTION MODEL
# ============================================================

class MessageReaction(Base):
    __tablename__ = "message_reactions"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # REACTION
    # ============================================================
    emoji = Column(String(20), nullable=False)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_message_reactions_unique', 'message_id', 'user_id', 'emoji', unique=True),
        Index('ix_message_reactions_message', 'message_id'),
        Index('ix_message_reactions_user', 'user_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    message = relationship(
        "Message",
        back_populates="reactions",
        foreign_keys=[message_id]
    )
    
    user = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<MessageReaction {self.id}: {self.emoji} - {self.user_id} -> {self.message_id}>"


# ============================================================
# 5. COURSE CHAT ROOM (Course-specific chat)
# ============================================================

class CourseChatRoom(Base):
    """Course-specific chat rooms."""
    __tablename__ = "course_chat_rooms"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # ============================================================
    # STATISTICS
    # ============================================================
    message_count = Column(Integer, default=0, nullable=False)
    participant_count = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship("Course", foreign_keys=[course_id])
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<CourseChatRoom {self.id}: {self.name}>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "course_id": self.course_id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "participant_count": self.participant_count,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# 6. COURSE CHAT MESSAGE
# ============================================================

class CourseChatMessage(Base):
    """Messages in course chat rooms."""
    __tablename__ = "course_chat_messages"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    room_id = Column(Integer, ForeignKey("course_chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # ============================================================
    # CONTENT
    # ============================================================
    content = Column(Text, nullable=False)
    
    # NEW: Message type
    message_type = Column(
        String(50),
        default=MessageType.TEXT.value,
        nullable=False
    )
    
    # NEW: Attachments
    attachments = Column(JSON, nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # MENTIONS
    # ============================================================
    mentioned_users = Column(JSON, nullable=True)  # List of user IDs mentioned
    
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
        Index('ix_course_chat_messages_room', 'room_id'),
        Index('ix_course_chat_messages_sender', 'sender_id'),
        Index('ix_course_chat_messages_created', 'created_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    room = relationship(
        "CourseChatRoom",
        foreign_keys=[room_id]
    )
    
    sender = relationship(
        "User",
        back_populates="course_chat_messages",
        foreign_keys=[sender_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<CourseChatMessage {self.id}: {self.content[:50]}...>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "sender_avatar": self.sender.profile_picture if self.sender else None,
            "content": self.content,
            "message_type": self.message_type,
            "attachments": self.attachments,
            "mentioned_users": self.mentioned_users,
            "is_deleted": self.is_deleted,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }