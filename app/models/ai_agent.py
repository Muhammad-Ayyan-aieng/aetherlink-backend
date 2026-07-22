# ============================================================
# AETHER LINK - AI AGENT MODEL (AI Hub)
# ============================================================
# Purpose: Manage AI agents, subscriptions, API access, and training data
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class AIAgentStatus(str, enum.Enum):
    """AI agent status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AIAgentPricingType(str, enum.Enum):
    """AI agent pricing type enumeration."""
    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    FREEMIUM = "freemium"


class AIAgentCategory(str, enum.Enum):
    """AI agent category enumeration."""
    CHATBOT = "chatbot"
    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    CONTENT = "content"
    CODING = "coding"
    DESIGN = "design"
    RESEARCH = "research"
    CUSTOMER_SERVICE = "customer_service"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OTHER = "other"


class AISubscriptionStatus(str, enum.Enum):
    """AI subscription status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    SUSPENDED = "suspended"


class AITrainingDataType(str, enum.Enum):
    """AI training data type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"  # CSV, JSON, etc.
    UNSTRUCTURED = "unstructured"


class AIApiKeyStatus(str, enum.Enum):
    """API key status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ============================================================
# 1. AI AGENT MODEL
# ============================================================

class AIAgent(Base):
    __tablename__ = "ai_agents"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(200), nullable=True)
    
    # ============================================================
    # CATEGORY & TYPE
    # ============================================================
    category = Column(
        String(50),
        default=AIAgentCategory.OTHER.value,
        nullable=False,
        index=True
    )
    
    # NEW: Sub-category
    sub_category = Column(String(50), nullable=True)
    
    # ============================================================
    # PRICING
    # ============================================================
    pricing_type = Column(
        String(20),
        default=AIAgentPricingType.SUBSCRIPTION.value,
        nullable=False
    )
    
    price = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    currency = Column(String(3), default="PKR", nullable=False)
    
    # NEW: Trial period (days)
    trial_days = Column(Integer, default=0, nullable=False)
    
    # NEW: Usage limits (for usage-based pricing)
    usage_limit = Column(Integer, nullable=True)  # per month
    usage_price_per_unit = Column(DECIMAL(10, 2), nullable=True)
    
    # ============================================================
    # CAPABILITIES
    # ============================================================
    capabilities = Column(JSON, nullable=True)
    # Example: ["text_generation", "image_generation", "voice_recognition"]
    
    # NEW: Input/output specifications
    input_spec = Column(JSON, nullable=True)
    output_spec = Column(JSON, nullable=True)
    
    # NEW: Supported languages
    supported_languages = Column(JSON, nullable=True)  # ["en", "ur", "ar"]
    
    # ============================================================
    # MEDIA
    # ============================================================
    icon_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=AIAgentStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    is_verified = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # STATISTICS (Cached)
    # ============================================================
    total_subscriptions = Column(Integer, default=0, nullable=False)
    active_subscriptions = Column(Integer, default=0, nullable=False)
    total_api_calls = Column(BigInteger, default=0, nullable=False)
    average_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # CREATOR
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Last updated by
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_ai_agents_category', 'category'),
        Index('ix_ai_agents_status', 'status'),
        Index('ix_ai_agents_pricing_type', 'pricing_type'),
        Index('ix_ai_agents_created_by', 'created_by'),
        Index('ix_ai_agents_slug', 'slug'),
        Index('ix_ai_agents_featured', 'is_featured'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    created_by_user = relationship(
        "User",
        back_populates="ai_agents_created",
        foreign_keys=[created_by]
    )
    
    # NEW: Updated by user
    updated_by_user = relationship(
        "User",
        foreign_keys=[updated_by],
        uselist=False
    )
    
    # NEW: Subscriptions
    subscriptions = relationship(
        "AIAgentSubscription",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    # NEW: Training data
    training_data = relationship(
        "AITrainingData",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    # NEW: API keys (for agent access)
    api_keys = relationship(
        "AIApiKey",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    # NEW: Reviews
    reviews = relationship(
        "AIAgentReview",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<AIAgent {self.id}: {self.name}>"
    
    def __str__(self) -> str:
        return self.name
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_draft(self) -> bool:
        """Check if agent is draft."""
        return self.status == AIAgentStatus.DRAFT.value
    
    @property
    def is_published_agent(self) -> bool:
        """Check if agent is published."""
        return self.status == AIAgentStatus.PUBLISHED.value
    
    @property
    def is_deprecated(self) -> bool:
        """Check if agent is deprecated."""
        return self.status == AIAgentStatus.DEPRECATED.value
    
    @property
    def is_archived_agent(self) -> bool:
        """Check if agent is archived."""
        return self.status == AIAgentStatus.ARCHIVED.value
    
    @property
    def is_free(self) -> bool:
        """Check if agent is free."""
        return self.pricing_type == AIAgentPricingType.FREE.value
    
    @property
    def is_subscription_based(self) -> bool:
        """Check if agent is subscription-based."""
        return self.pricing_type == AIAgentPricingType.SUBSCRIPTION.value
    
    @property
    def is_usage_based(self) -> bool:
        """Check if agent is usage-based."""
        return self.pricing_type == AIAgentPricingType.USAGE_BASED.value
    
    @property
    def display_category(self) -> str:
        """Get human-readable category."""
        category_map = {
            "chatbot": "💬 Chatbot",
            "automation": "⚡ Automation",
            "analytics": "📊 Analytics",
            "content": "📝 Content",
            "coding": "💻 Coding",
            "design": "🎨 Design",
            "research": "🔬 Research",
            "customer_service": "👥 Customer Service",
            "marketing": "📢 Marketing",
            "sales": "💰 Sales",
            "hr": "👔 HR",
            "finance": "🏦 Finance",
            "other": "📌 Other",
        }
        return category_map.get(self.category, "Other")
    
    @property
    def display_pricing(self) -> str:
        """Get human-readable pricing."""
        if self.is_free:
            return "🆓 Free"
        elif self.is_subscription_based:
            return f"🔄 {self.price}/month"
        elif self.pricing_type == AIAgentPricingType.ONE_TIME.value:
            return f"💳 {self.price} one-time"
        elif self.is_usage_based:
            return f"📊 Usage-based"
        return "Unknown"
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "draft": "📝 Draft",
            "published": "🚀 Published",
            "deprecated": "⚠️ Deprecated",
            "archived": "📦 Archived",
            "deleted": "🗑️ Deleted",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_api_calls == 0:
            return 0.0
        # This would need error count from logs
        return 0.0  # Placeholder
    
    @property
    def is_popular(self) -> bool:
        """Check if agent is popular."""
        return self.total_subscriptions >= 100
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def publish(self) -> None:
        """Publish the AI agent."""
        self.status = AIAgentStatus.PUBLISHED.value
        self.published_at = func.now()
    
    def deprecate(self) -> None:
        """Deprecate the AI agent."""
        self.status = AIAgentStatus.DEPRECATED.value
    
    def archive_agent(self) -> None:
        """Archive the AI agent."""
        self.status = AIAgentStatus.ARCHIVED.value
    
    def soft_delete_agent(self) -> None:
        """Soft delete the AI agent."""
        self.status = AIAgentStatus.DELETED.value
        self.deleted_at = func.now()
    
    def restore_agent(self) -> None:
        """Restore a soft-deleted agent."""
        self.status = AIAgentStatus.DRAFT.value
        self.deleted_at = None
    
    def increment_subscription(self) -> None:
        """Increment subscription count."""
        self.total_subscriptions += 1
        self.active_subscriptions += 1
    
    def decrement_subscription(self) -> None:
        """Decrement subscription count."""
        if self.total_subscriptions > 0:
            self.total_subscriptions -= 1
        if self.active_subscriptions > 0:
            self.active_subscriptions -= 1
    
    def increment_api_calls(self, count: int = 1) -> None:
        """Increment API call count."""
        self.total_api_calls += count
    
    def update_rating(self, new_rating: float) -> None:
        """Update average rating with a new review."""
        total = self.average_rating * self.total_reviews
        self.total_reviews += 1
        if self.total_reviews > 0:
            self.average_rating = (total + new_rating) / self.total_reviews
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert AI agent to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "category": self.category,
            "display_category": self.display_category,
            "sub_category": self.sub_category,
            "pricing_type": self.pricing_type,
            "display_pricing": self.display_pricing,
            "price": float(self.price) if self.price else 0.0,
            "currency": self.currency,
            "is_free": self.is_free,
            "trial_days": self.trial_days,
            "capabilities": self.capabilities,
            "supported_languages": self.supported_languages,
            "icon_url": self.icon_url,
            "banner_url": self.banner_url,
            "demo_url": self.demo_url,
            "documentation_url": self.documentation_url,
            "status": self.status,
            "display_status": self.display_status,
            "is_verified": self.is_verified,
            "is_featured": self.is_featured,
            "total_subscriptions": self.total_subscriptions,
            "active_subscriptions": self.active_subscriptions,
            "total_api_calls": self.total_api_calls,
            "average_rating": float(self.average_rating) if self.average_rating else 0.0,
            "total_reviews": self.total_reviews,
            "is_popular": self.is_popular,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
        
        if include_sensitive:
            data.update({
                "input_spec": self.input_spec,
                "output_spec": self.output_spec,
                "usage_limit": self.usage_limit,
                "usage_price_per_unit": float(self.usage_price_per_unit) if self.usage_price_per_unit else None,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing AI agent data."""
        data = self.to_dict()
        data.pop("input_spec", None)
        data.pop("output_spec", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing AI agent data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. AI AGENT SUBSCRIPTION MODEL
# ============================================================

class AIAgentSubscription(Base):
    __tablename__ = "ai_agent_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Subscription details
    status = Column(
        String(20),
        default=AISubscriptionStatus.TRIAL.value,
        nullable=False,
        index=True
    )
    
    # NEW: Pricing at time of subscription
    price = Column(DECIMAL(10, 2), nullable=False)
    billing_cycle = Column(String(20), nullable=True)  # monthly, yearly
    
    # NEW: Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    usage_limit = Column(Integer, nullable=True)
    
    # DATES
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Payment reference
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    
    # NEW: Auto-renewal
    auto_renew = Column(Boolean, default=True, nullable=False)
    
    # NEW: Metadata
    metadata = Column(JSON, nullable=True)
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_ai_subscriptions_unique', 'agent_id', 'user_id', unique=True),
        Index('ix_ai_subscriptions_agent', 'agent_id'),
        Index('ix_ai_subscriptions_user', 'user_id'),
        Index('ix_ai_subscriptions_status', 'status'),
        Index('ix_ai_subscriptions_expires_at', 'expires_at'),
    )
    
    # RELATIONSHIPS
    agent = relationship(
        "AIAgent",
        back_populates="subscriptions",
        foreign_keys=[agent_id]
    )
    
    user = relationship(
        "User",
        back_populates="ai_agent_subscriptions",
        foreign_keys=[user_id]
    )
    
    payment = relationship(
        "Payment",
        foreign_keys=[payment_id],
        uselist=False
    )
    
    # NEW: API keys
    api_keys = relationship(
        "AIApiKey",
        back_populates="subscription",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AIAgentSubscription {self.id}: {self.user_id} -> {self.agent_id}>"
    
    @property
    def is_active_subscription(self) -> bool:
        """Check if subscription is active."""
        return self.status == AISubscriptionStatus.ACTIVE.value and not self.is_expired
    
    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial."""
        return self.status == AISubscriptionStatus.TRIAL.value
    
    @property
    def is_expired_subscription(self) -> bool:
        """Check if subscription is expired."""
        if self.expires_at is None:
            return False
        return self.expires_at <= func.now()
    
    @property
    def is_cancelled_subscription(self) -> bool:
        """Check if subscription is cancelled."""
        return self.status == AISubscriptionStatus.CANCELLED.value
    
    @property
    def is_suspended(self) -> bool:
        """Check if subscription is suspended."""
        return self.status == AISubscriptionStatus.SUSPENDED.value
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until subscription expiry."""
        if self.expires_at is None:
            return -1
        delta = self.expires_at - func.now()
        return max(0, delta.days)
    
    @property
    def usage_remaining(self) -> int:
        """Get remaining usage."""
        if self.usage_limit is None:
            return -1
        return max(0, self.usage_limit - self.usage_count)
    
    @property
    def is_over_usage_limit(self) -> bool:
        """Check if usage is over limit."""
        if self.usage_limit is None:
            return False
        return self.usage_count >= self.usage_limit
    
    def activate(self) -> None:
        """Activate subscription."""
        self.status = AISubscriptionStatus.ACTIVE.value
        self.trial_ends_at = None
    
    def cancel(self) -> None:
        """Cancel subscription."""
        self.status = AISubscriptionStatus.CANCELLED.value
        self.cancelled_at = func.now()
        self.auto_renew = False
    
    def suspend(self) -> None:
        """Suspend subscription."""
        self.status = AISubscriptionStatus.SUSPENDED.value
        self.suspended_at = func.now()
    
    def resume(self) -> None:
        """Resume subscription."""
        self.status = AISubscriptionStatus.ACTIVE.value
        self.suspended_at = None
    
    def expire_subscription(self) -> None:
        """Expire subscription."""
        self.status = AISubscriptionStatus.EXPIRED.value
    
    def increment_usage(self, count: int = 1) -> None:
        """Increment usage count."""
        self.usage_count += count
    
    def set_usage_limit(self, limit: int) -> None:
        """Set usage limit."""
        self.usage_limit = limit
    
    def extend_trial(self, days: int) -> None:
        """Extend trial period."""
        self.trial_ends_at = func.now() + func.interval(f'{days} days')
        self.status = AISubscriptionStatus.TRIAL.value
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "status": self.status,
            "is_active": self.is_active_subscription,
            "is_trial": self.is_trial,
            "is_expired": self.is_expired_subscription,
            "is_cancelled": self.is_cancelled_subscription,
            "price": float(self.price) if self.price else 0.0,
            "billing_cycle": self.billing_cycle,
            "usage_count": self.usage_count,
            "usage_limit": self.usage_limit,
            "usage_remaining": self.usage_remaining,
            "auto_renew": self.auto_renew,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "days_until_expiry": self.days_until_expiry,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_sensitive:
            data.update({
                "payment_id": self.payment_id,
                "suspended_at": self.suspended_at.isoformat() if self.suspended_at else None,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data


# ============================================================
# 3. AI TRAINING DATA MODEL
# ============================================================

class AITrainingData(Base):
    __tablename__ = "ai_training_data"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    data_type = Column(
        String(50),
        default=AITrainingDataType.TEXT.value,
        nullable=False
    )
    
    # NEW: File information
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # NEW: Data statistics
    record_count = Column(Integer, nullable=True)
    data_size = Column(BigInteger, nullable=True)  # In bytes
    
    # NEW: Metadata
    metadata = Column(JSON, nullable=True)
    
    # NEW: Uploaded by
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Status
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, ready, failed
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_ai_training_data_agent', 'agent_id'),
        Index('ix_ai_training_data_type', 'data_type'),
        Index('ix_ai_training_data_status', 'status'),
        Index('ix_ai_training_data_uploaded_by', 'uploaded_by'),
    )
    
    # RELATIONSHIPS
    agent = relationship(
        "AIAgent",
        back_populates="training_data",
        foreign_keys=[agent_id]
    )
    
    uploaded_by_user = relationship(
        "User",
        back_populates="ai_training_data_uploaded",
        foreign_keys=[uploaded_by]
    )
    
    def __repr__(self) -> str:
        return f"<AITrainingData {self.id}: {self.name}>"
    
    @property
    def display_type(self) -> str:
        type_map = {
            "text": "📝 Text",
            "image": "🖼️ Image",
            "audio": "🎵 Audio",
            "video": "🎬 Video",
            "structured": "📊 Structured",
            "unstructured": "📄 Unstructured",
        }
        return type_map.get(self.data_type, "Unknown")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "name": self.name,
            "description": self.description,
            "data_type": self.data_type,
            "display_type": self.display_type,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "record_count": self.record_count,
            "data_size": self.data_size,
            "status": self.status,
            "uploaded_by": self.uploaded_by,
            "uploaded_by_name": self.uploaded_by_user.full_name if self.uploaded_by_user else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# 4. AI API KEY MODEL
# ============================================================

class AIApiKey(Base):
    __tablename__ = "ai_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("ai_agent_subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Agent (if key is for a specific agent)
    agent_id = Column(Integer, ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # API key
    api_key = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=True)
    
    # NEW: Permissions
    permissions = Column(JSON, nullable=True)
    # Example: {"read": true, "write": true, "delete": false}
    
    # NEW: Rate limiting
    rate_limit_per_minute = Column(Integer, default=100, nullable=False)
    rate_limit_per_day = Column(Integer, nullable=True)
    
    # NEW: Last used
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_used_ip = Column(String(100), nullable=True)
    
    # NEW: Status
    status = Column(
        String(20),
        default=AIApiKeyStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    # DATES
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_ai_api_keys_user', 'user_id'),
        Index('ix_ai_api_keys_subscription', 'subscription_id'),
        Index('ix_ai_api_keys_agent', 'agent_id'),
        Index('ix_ai_api_keys_status', 'status'),
        Index('ix_ai_api_keys_key', 'api_key'),
    )
    
    # RELATIONSHIPS
    user = relationship(
        "User",
        back_populates="ai_api_keys",
        foreign_keys=[user_id]
    )
    
    subscription = relationship(
        "AIAgentSubscription",
        back_populates="api_keys",
        foreign_keys=[subscription_id]
    )
    
    agent = relationship(
        "AIAgent",
        foreign_keys=[agent_id]
    )
    
    # NEW: API logs
    logs = relationship(
        "AIApiLog",
        back_populates="api_key",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AIApiKey {self.id}: {self.api_key[:8]}...>"
    
    @property
    def is_active_key(self) -> bool:
        """Check if API key is active."""
        return self.status == AIApiKeyStatus.ACTIVE.value and not self.is_expired_key
    
    @property
    def is_expired_key(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return self.expires_at <= func.now()
    
    @property
    def is_revoked_key(self) -> bool:
        """Check if API key is revoked."""
        return self.status == AIApiKeyStatus.REVOKED.value
    
    @property
    def display_status(self) -> str:
        status_map = {
            "active": "🟢 Active",
            "inactive": "⚪ Inactive",
            "revoked": "🔴 Revoked",
            "expired": "⏰ Expired",
        }
        return status_map.get(self.status, "Unknown")
    
    def revoke(self) -> None:
        """Revoke API key."""
        self.status = AIApiKeyStatus.REVOKED.value
        self.revoked_at = func.now()
    
    def activate_key(self) -> None:
        """Activate API key."""
        self.status = AIApiKeyStatus.ACTIVE.value
        self.revoked_at = None
    
    def mark_used(self, ip_address: str) -> None:
        """Mark API key as used."""
        self.last_used_at = func.now()
        self.last_used_ip = ip_address
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "subscription_id": self.subscription_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "api_key": self.api_key,
            "name": self.name,
            "permissions": self.permissions,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_day": self.rate_limit_per_day,
            "status": self.status,
            "display_status": self.display_status,
            "is_active": self.is_active_key,
            "is_expired": self.is_expired_key,
            "is_revoked": self.is_revoked_key,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_used_ip": self.last_used_ip,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# 5. AI API LOG MODEL
# ============================================================

class AIApiLog(Base):
    __tablename__ = "ai_api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("ai_api_keys.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Request details
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    
    # NEW: Request/Response
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # NEW: Metrics
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    # NEW: Status
    status_code = Column(Integer, nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # NEW: Cost
    cost = Column(DECIMAL(10, 4), nullable=True)  # Cost for this API call
    
    # NEW: Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_ai_api_logs_api_key', 'api_key_id'),
        Index('ix_ai_api_logs_user', 'user_id'),
        Index('ix_ai_api_logs_agent', 'agent_id'),
        Index('ix_ai_api_logs_status_code', 'status_code'),
        Index('ix_ai_api_logs_success', 'success'),
        Index('ix_ai_api_logs_endpoint', 'endpoint'),
    )
    
    # RELATIONSHIPS
    api_key = relationship(
        "AIApiKey",
        back_populates="logs",
        foreign_keys=[api_key_id]
    )
    
    user = relationship(
        "User",
        back_populates="ai_api_logs",
        foreign_keys=[user_id]
    )
    
    agent = relationship(
        "AIAgent",
        foreign_keys=[agent_id]
    )
    
    def __repr__(self) -> str:
        return f"<AIApiLog {self.id}: {self.endpoint} - {self.status_code}>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "api_key_id": self.api_key_id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "endpoint": self.endpoint,
            "method": self.method,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "latency_ms": self.latency_ms,
            "status_code": self.status_code,
            "success": self.success,
            "error_message": self.error_message,
            "cost": float(self.cost) if self.cost else None,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }