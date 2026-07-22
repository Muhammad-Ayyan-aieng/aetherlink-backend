# ============================================================
# AETHER LINK - AI AGENT SCHEMAS (AI Hub)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# AI AGENT ENUMS
# ============================================================

class AIAgentStatusEnum(str, Enum):
    """AI agent status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AIAgentPricingTypeEnum(str, Enum):
    """AI agent pricing type enumeration."""
    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    FREEMIUM = "freemium"


class AIAgentCategoryEnum(str, Enum):
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


class AISubscriptionStatusEnum(str, Enum):
    """AI subscription status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    SUSPENDED = "suspended"


class AITrainingDataTypeEnum(str, Enum):
    """AI training data type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"


class AIApiKeyStatusEnum(str, Enum):
    """API key status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ============================================================
# BASE SCHEMA
# ============================================================

class AIAgentBase(BaseModel):
    """Base AI agent schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# AI AGENT SCHEMAS
# ============================================================

class AIAgentCreate(AIAgentBase):
    """Schema for creating an AI agent."""
    
    name: str = Field(..., min_length=3, max_length=100, description="Agent name")
    slug: str = Field(..., min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=5000, description="Agent description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description")
    
    category: AIAgentCategoryEnum = Field(
        default=AIAgentCategoryEnum.OTHER,
        description="Agent category"
    )
    sub_category: Optional[str] = Field(default=None, max_length=50, description="Sub-category")
    
    pricing_type: AIAgentPricingTypeEnum = Field(
        default=AIAgentPricingTypeEnum.SUBSCRIPTION,
        description="Pricing type"
    )
    price: float = Field(default=0.0, ge=0, description="Price")
    currency: str = Field(default="PKR", max_length=3, description="Currency code")
    trial_days: int = Field(default=0, ge=0, description="Trial period in days")
    
    usage_limit: Optional[int] = Field(default=None, ge=0, description="Usage limit per month")
    usage_price_per_unit: Optional[float] = Field(default=None, ge=0, description="Price per usage unit")
    
    capabilities: Optional[List[str]] = Field(
        default=None,
        description="Agent capabilities"
    )
    input_spec: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Input specification"
    )
    output_spec: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Output specification"
    )
    supported_languages: Optional[List[str]] = Field(
        default=None,
        description="Supported languages"
    )
    
    icon_url: Optional[str] = Field(default=None, max_length=500, description="Icon URL")
    banner_url: Optional[str] = Field(default=None, max_length=500, description="Banner URL")
    demo_url: Optional[str] = Field(default=None, max_length=500, description="Demo URL")
    documentation_url: Optional[str] = Field(default=None, max_length=500, description="Documentation URL")
    
    status: AIAgentStatusEnum = Field(
        default=AIAgentStatusEnum.DRAFT,
        description="Agent status"
    )
    is_verified: bool = Field(default=False, description="Is verified")
    is_featured: bool = Field(default=False, description="Is featured")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()


class AIAgentUpdate(AIAgentBase):
    """Schema for updating an AI agent."""
    
    name: Optional[str] = Field(default=None, min_length=3, max_length=100, description="Agent name")
    slug: Optional[str] = Field(default=None, min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=5000, description="Agent description")
    short_description: Optional[str] = Field(default=None, max_length=200, description="Short description")
    
    category: Optional[AIAgentCategoryEnum] = Field(default=None, description="Agent category")
    sub_category: Optional[str] = Field(default=None, max_length=50, description="Sub-category")
    
    pricing_type: Optional[AIAgentPricingTypeEnum] = Field(default=None, description="Pricing type")
    price: Optional[float] = Field(default=None, ge=0, description="Price")
    currency: Optional[str] = Field(default=None, max_length=3, description="Currency code")
    trial_days: Optional[int] = Field(default=None, ge=0, description="Trial period in days")
    
    usage_limit: Optional[int] = Field(default=None, ge=0, description="Usage limit per month")
    usage_price_per_unit: Optional[float] = Field(default=None, ge=0, description="Price per usage unit")
    
    capabilities: Optional[List[str]] = Field(default=None, description="Agent capabilities")
    input_spec: Optional[Dict[str, Any]] = Field(default=None, description="Input specification")
    output_spec: Optional[Dict[str, Any]] = Field(default=None, description="Output specification")
    supported_languages: Optional[List[str]] = Field(default=None, description="Supported languages")
    
    icon_url: Optional[str] = Field(default=None, max_length=500, description="Icon URL")
    banner_url: Optional[str] = Field(default=None, max_length=500, description="Banner URL")
    demo_url: Optional[str] = Field(default=None, max_length=500, description="Demo URL")
    documentation_url: Optional[str] = Field(default=None, max_length=500, description="Documentation URL")
    
    status: Optional[AIAgentStatusEnum] = Field(default=None, description="Agent status")
    is_verified: Optional[bool] = Field(default=None, description="Is verified")
    is_featured: Optional[bool] = Field(default=None, description="Is featured")


class AIAgentPublish(AIAgentBase):
    """Schema for publishing an AI agent."""
    
    publish: bool = Field(..., description="True to publish, False to unpublish")


# ============================================================
# AI AGENT SUBSCRIPTION SCHEMAS
# ============================================================

class AIAgentSubscribe(AIAgentBase):
    """Schema for subscribing to an AI agent."""
    
    agent_id: int = Field(..., gt=0, description="Agent ID")
    billing_cycle: str = Field(default="monthly", description="Billing cycle (monthly, yearly)")
    auto_renew: bool = Field(default=True, description="Auto-renew subscription")


class AIAgentSubscriptionUpdate(AIAgentBase):
    """Schema for updating an AI subscription."""
    
    status: Optional[AISubscriptionStatusEnum] = Field(default=None, description="Subscription status")
    auto_renew: Optional[bool] = Field(default=None, description="Auto-renew")


class AIAgentSubscriptionCancel(AIAgentBase):
    """Schema for cancelling an AI subscription."""
    
    subscription_id: int = Field(..., gt=0, description="Subscription ID")
    reason: Optional[str] = Field(default=None, max_length=500, description="Cancellation reason")


# ============================================================
# AI TRAINING DATA SCHEMAS
# ============================================================

class AITrainingDataCreate(AIAgentBase):
    """Schema for creating AI training data."""
    
    agent_id: Optional[int] = Field(default=None, gt=0, description="Agent ID")
    name: str = Field(..., min_length=3, max_length=255, description="Data name")
    description: Optional[str] = Field(default=None, max_length=500, description="Data description")
    
    data_type: AITrainingDataTypeEnum = Field(..., description="Data type")
    
    file_url: Optional[str] = Field(default=None, max_length=500, description="File URL")
    file_name: Optional[str] = Field(default=None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, max_length=100, description="MIME type")
    
    record_count: Optional[int] = Field(default=None, ge=0, description="Record count")
    data_size: Optional[int] = Field(default=None, ge=0, description="Data size in bytes")
    
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AITrainingDataUpdate(AIAgentBase):
    """Schema for updating AI training data."""
    
    name: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Data name")
    description: Optional[str] = Field(default=None, max_length=500, description="Data description")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AITrainingDataResponse(AIAgentBase):
    """Schema for training data response."""
    
    id: int = Field(..., description="Training data ID")
    agent_id: Optional[int] = Field(default=None, description="Agent ID")
    agent_name: Optional[str] = Field(default=None, description="Agent name")
    
    name: str = Field(..., description="Data name")
    description: Optional[str] = Field(default=None, description="Data description")
    
    data_type: str = Field(..., description="Data type")
    display_type: str = Field(..., description="Human-readable type")
    
    file_url: Optional[str] = Field(default=None, description="File URL")
    file_name: Optional[str] = Field(default=None, description="Original file name")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    
    record_count: Optional[int] = Field(default=None, description="Record count")
    data_size: Optional[int] = Field(default=None, description="Data size in bytes")
    
    status: str = Field(..., description="Data status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    uploaded_by: Optional[int] = Field(default=None, description="Uploaded by user ID")
    uploaded_by_name: Optional[str] = Field(default=None, description="Uploaded by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# AI API KEY SCHEMAS
# ============================================================

class AIApiKeyCreate(AIAgentBase):
    """Schema for creating an AI API key."""
    
    agent_id: Optional[int] = Field(default=None, gt=0, description="Agent ID")
    subscription_id: Optional[int] = Field(default=None, gt=0, description="Subscription ID")
    
    name: Optional[str] = Field(default=None, max_length=100, description="API key name")
    
    permissions: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Permissions"
    )
    rate_limit_per_minute: int = Field(default=100, ge=1, description="Rate limit per minute")
    rate_limit_per_day: Optional[int] = Field(default=None, ge=1, description="Rate limit per day")
    
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")


class AIApiKeyUpdate(AIAgentBase):
    """Schema for updating an AI API key."""
    
    name: Optional[str] = Field(default=None, max_length=100, description="API key name")
    permissions: Optional[Dict[str, bool]] = Field(default=None, description="Permissions")
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, description="Rate limit per minute")
    rate_limit_per_day: Optional[int] = Field(default=None, ge=1, description="Rate limit per day")
    status: Optional[AIApiKeyStatusEnum] = Field(default=None, description="API key status")


class AIApiKeyRevoke(AIAgentBase):
    """Schema for revoking an AI API key."""
    
    api_key_id: int = Field(..., gt=0, description="API key ID")
    reason: Optional[str] = Field(default=None, max_length=500, description="Revocation reason")


class AIApiKeyResponse(AIAgentBase):
    """Schema for API key response."""
    
    id: int = Field(..., description="API key ID")
    user_id: int = Field(..., description="User ID")
    user_name: Optional[str] = Field(default=None, description="User name")
    
    subscription_id: Optional[int] = Field(default=None, description="Subscription ID")
    agent_id: Optional[int] = Field(default=None, description="Agent ID")
    agent_name: Optional[str] = Field(default=None, description="Agent name")
    
    api_key: str = Field(..., description="API key (only shown on creation)")
    name: Optional[str] = Field(default=None, description="API key name")
    
    permissions: Optional[Dict[str, bool]] = Field(default=None, description="Permissions")
    rate_limit_per_minute: int = Field(..., description="Rate limit per minute")
    rate_limit_per_day: Optional[int] = Field(default=None, description="Rate limit per day")
    
    status: str = Field(..., description="API key status")
    display_status: str = Field(..., description="Human-readable status")
    is_active: bool = Field(..., description="Is active")
    is_expired: bool = Field(..., description="Is expired")
    is_revoked: bool = Field(..., description="Is revoked")
    
    last_used_at: Optional[datetime] = Field(default=None, description="Last used timestamp")
    last_used_ip: Optional[str] = Field(default=None, description="Last used IP")
    
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    revoked_at: Optional[datetime] = Field(default=None, description="Revoked timestamp")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# AI API LOG SCHEMAS
# ============================================================

class AIApiLogResponse(AIAgentBase):
    """Schema for API log response."""
    
    id: int = Field(..., description="Log ID")
    api_key_id: Optional[int] = Field(default=None, description="API key ID")
    user_id: Optional[int] = Field(default=None, description="User ID")
    user_name: Optional[str] = Field(default=None, description="User name")
    agent_id: Optional[int] = Field(default=None, description="Agent ID")
    agent_name: Optional[str] = Field(default=None, description="Agent name")
    
    endpoint: str = Field(..., description="API endpoint")
    method: str = Field(..., description="HTTP method")
    
    request_size: Optional[int] = Field(default=None, description="Request size in bytes")
    response_size: Optional[int] = Field(default=None, description="Response size in bytes")
    latency_ms: Optional[int] = Field(default=None, description="Latency in milliseconds")
    
    status_code: int = Field(..., description="HTTP status code")
    success: bool = Field(..., description="Is success")
    error_message: Optional[str] = Field(default=None, description="Error message")
    
    cost: Optional[float] = Field(default=None, description="Cost for this API call")
    
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    
    created_at: datetime = Field(..., description="Creation timestamp")


# ============================================================
# AI AGENT RESPONSE SCHEMA
# ============================================================

class AIAgentResponse(AIAgentBase):
    """Schema for AI agent response."""
    
    id: int = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(default=None, description="Agent description")
    short_description: Optional[str] = Field(default=None, description="Short description")
    
    category: str = Field(..., description="Agent category")
    display_category: str = Field(..., description="Human-readable category")
    sub_category: Optional[str] = Field(default=None, description="Sub-category")
    
    pricing_type: str = Field(..., description="Pricing type")
    display_pricing: str = Field(..., description="Human-readable pricing")
    price: float = Field(..., description="Price")
    currency: str = Field(..., description="Currency code")
    is_free: bool = Field(..., description="Is free")
    trial_days: int = Field(..., description="Trial period in days")
    
    capabilities: Optional[List[str]] = Field(default=None, description="Agent capabilities")
    supported_languages: Optional[List[str]] = Field(default=None, description="Supported languages")
    
    icon_url: Optional[str] = Field(default=None, description="Icon URL")
    banner_url: Optional[str] = Field(default=None, description="Banner URL")
    demo_url: Optional[str] = Field(default=None, description="Demo URL")
    documentation_url: Optional[str] = Field(default=None, description="Documentation URL")
    
    status: str = Field(..., description="Agent status")
    display_status: str = Field(..., description="Human-readable status")
    is_verified: bool = Field(..., description="Is verified")
    is_featured: bool = Field(..., description="Is featured")
    is_popular: bool = Field(..., description="Is popular")
    
    total_subscriptions: int = Field(..., description="Total subscriptions")
    active_subscriptions: int = Field(..., description="Active subscriptions")
    total_api_calls: int = Field(..., description="Total API calls")
    average_rating: float = Field(..., description="Average rating")
    total_reviews: int = Field(..., description="Total reviews")
    success_rate: float = Field(..., description="Success rate")
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")


# ============================================================
# AI AGENT DETAIL RESPONSE
# ============================================================

class AIAgentDetailResponse(AIAgentResponse):
    """Schema for AI agent detail response."""
    
    # NEW: Subscription info for current user
    user_subscription: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current user's subscription"
    )
    user_is_subscribed: bool = Field(default=False, description="User is subscribed")
    user_can_subscribe: bool = Field(default=True, description="User can subscribe")


# ============================================================
# AI AGENT LIST REQUEST (Filters)
# ============================================================

class AIAgentListRequest(AIAgentBase):
    """Schema for AI agent list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by name or description")
    category: Optional[AIAgentCategoryEnum] = Field(default=None, description="Filter by category")
    pricing_type: Optional[AIAgentPricingTypeEnum] = Field(default=None, description="Filter by pricing type")
    status: Optional[AIAgentStatusEnum] = Field(default=None, description="Filter by status")
    is_verified: Optional[bool] = Field(default=None, description="Filter by verified")
    is_featured: Optional[bool] = Field(default=None, description="Filter by featured")
    price_min: Optional[float] = Field(default=None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(default=None, ge=0, description="Maximum price")
    created_by: Optional[int] = Field(default=None, description="Filter by creator")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# AI AGENT LIST RESPONSE
# ============================================================

class AIAgentListResponse(AIAgentBase):
    """Schema for paginated AI agent list response."""
    
    agents: List[AIAgentResponse] = Field(..., description="List of AI agents")
    total: int = Field(..., description="Total agents")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# AI AGENT STATISTICS (Admin View)
# ============================================================

class AIAgentStatistics(AIAgentBase):
    """Schema for AI agent statistics."""
    
    total_agents: int = Field(..., description="Total agents")
    draft: int = Field(..., description="Draft agents")
    published: int = Field(..., description="Published agents")
    deprecated: int = Field(..., description="Deprecated agents")
    archived: int = Field(..., description="Archived agents")
    
    # NEW: Category breakdown
    category_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Agents by category"
    )
    
    # NEW: Pricing breakdown
    pricing_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Agents by pricing type"
    )
    
    # NEW: Subscription stats
    total_subscriptions: int = Field(..., description="Total subscriptions")
    active_subscriptions: int = Field(..., description="Active subscriptions")
    trial_subscriptions: int = Field(..., description="Trial subscriptions")
    
    # NEW: Revenue stats
    total_revenue: float = Field(..., description="Total revenue from agents")
    average_price: float = Field(..., description="Average agent price")
    
    # NEW: API stats
    total_api_calls: int = Field(..., description="Total API calls")
    successful_api_calls: int = Field(..., description="Successful API calls")
    failed_api_calls: int = Field(..., description="Failed API calls")
    average_success_rate: float = Field(..., description="Average success rate")
    
    # NEW: Top agents
    top_agents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top performing agents"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily subscription trends"
    )


# ============================================================
# AI API USAGE STATISTICS
# ============================================================

class AIApiUsageStatistics(AIAgentBase):
    """Schema for API usage statistics."""
    
    total_requests: int = Field(..., description="Total API requests")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    average_latency_ms: float = Field(..., description="Average latency in milliseconds")
    
    # NEW: By agent
    agent_usage: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage by agent"
    )
    
    # NEW: By user
    user_usage: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage by user"
    )
    
    # NEW: By endpoint
    endpoint_usage: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage by endpoint"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily API usage trends"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "AIAgentStatusEnum",
    "AIAgentPricingTypeEnum",
    "AIAgentCategoryEnum",
    "AISubscriptionStatusEnum",
    "AITrainingDataTypeEnum",
    "AIApiKeyStatusEnum",
    "AIAgentCreate",
    "AIAgentUpdate",
    "AIAgentPublish",
    "AIAgentSubscribe",
    "AIAgentSubscriptionUpdate",
    "AIAgentSubscriptionCancel",
    "AITrainingDataCreate",
    "AITrainingDataUpdate",
    "AITrainingDataResponse",
    "AIApiKeyCreate",
    "AIApiKeyUpdate",
    "AIApiKeyRevoke",
    "AIApiKeyResponse",
    "AIApiLogResponse",
    "AIAgentResponse",
    "AIAgentDetailResponse",
    "AIAgentListRequest",
    "AIAgentListResponse",
    "AIAgentStatistics",
    "AIApiUsageStatistics",
]