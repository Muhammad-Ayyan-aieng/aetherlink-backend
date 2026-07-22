# ============================================================
# AETHER LINK - COUPON SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# COUPON ENUMS
# ============================================================

class CouponTypeEnum(str, Enum):
    """Coupon type enumeration."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class CouponStatusEnum(str, Enum):
    """Coupon status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    DEPLETED = "depleted"
    DELETED = "deleted"


class CouponTargetTypeEnum(str, Enum):
    """Coupon target type enumeration."""
    COURSE = "course"
    LEARNING_PATH = "learning_path"
    ALL = "all"


class CouponUsageStatusEnum(str, Enum):
    """Coupon usage status enumeration."""
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ============================================================
# BASE SCHEMA
# ============================================================

class CouponBase(BaseModel):
    """Base coupon schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# COUPON CREATE SCHEMA
# ============================================================

class CouponCreate(CouponBase):
    """Schema for creating a coupon."""
    
    code: str = Field(..., min_length=3, max_length=50, description="Coupon code (e.g., SUMMER20)")
    description: Optional[str] = Field(default=None, max_length=500, description="Coupon description")
    
    discount_type: CouponTypeEnum = Field(..., description="Discount type")
    discount_value: float = Field(..., gt=0, description="Discount value")
    max_discount_amount: Optional[float] = Field(default=None, gt=0, description="Maximum discount amount")
    min_purchase_amount: float = Field(default=0, ge=0, description="Minimum purchase amount")
    
    target_type: CouponTargetTypeEnum = Field(
        default=CouponTargetTypeEnum.ALL,
        description="Target type"
    )
    target_id: Optional[int] = Field(default=None, gt=0, description="Target ID (course or path)")
    
    usage_limit: Optional[int] = Field(default=None, gt=0, description="Usage limit (null = unlimited)")
    per_user_limit: int = Field(default=1, ge=1, description="Limit per user")
    first_time_only: bool = Field(default=False, description="First-time users only")
    
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    grace_period_days: int = Field(default=0, ge=0, description="Grace period days")
    
    status: CouponStatusEnum = Field(
        default=CouponStatusEnum.ACTIVE,
        description="Coupon status"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate coupon code format."""
        import re
        if not re.match(r'^[A-Z0-9\-_]{3,50}$', v):
            raise ValueError('Coupon code must contain only uppercase letters, numbers, hyphens, and underscores')
        return v.upper()
    
    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v: float, info: Dict[str, Any]) -> float:
        """Validate discount value based on type."""
        data = info.data
        discount_type = data.get('discount_type')
        if discount_type == CouponTypeEnum.PERCENTAGE and (v <= 0 or v > 100):
            raise ValueError('Percentage discount must be between 1 and 100')
        if discount_type == CouponTypeEnum.FIXED and v <= 0:
            raise ValueError('Fixed discount must be greater than 0')
        return v
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_dates(cls, v: datetime, info: Dict[str, Any]) -> datetime:
        """Validate date range."""
        if 'start_date' in info.data and 'end_date' in info.data:
            start = info.data['start_date']
            end = info.data['end_date']
            if start and end and end <= start:
                raise ValueError('End date must be after start date')
        return v


# ============================================================
# COUPON UPDATE SCHEMA
# ============================================================

class CouponUpdate(CouponBase):
    """Schema for updating a coupon."""
    
    description: Optional[str] = Field(default=None, max_length=500, description="Coupon description")
    
    discount_type: Optional[CouponTypeEnum] = Field(default=None, description="Discount type")
    discount_value: Optional[float] = Field(default=None, gt=0, description="Discount value")
    max_discount_amount: Optional[float] = Field(default=None, gt=0, description="Maximum discount amount")
    min_purchase_amount: Optional[float] = Field(default=None, ge=0, description="Minimum purchase amount")
    
    target_type: Optional[CouponTargetTypeEnum] = Field(default=None, description="Target type")
    target_id: Optional[int] = Field(default=None, gt=0, description="Target ID")
    
    usage_limit: Optional[int] = Field(default=None, gt=0, description="Usage limit")
    per_user_limit: Optional[int] = Field(default=None, ge=1, description="Limit per user")
    first_time_only: Optional[bool] = Field(default=None, description="First-time users only")
    
    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")
    grace_period_days: Optional[int] = Field(default=None, ge=0, description="Grace period days")
    
    status: Optional[CouponStatusEnum] = Field(default=None, description="Coupon status")
    
    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v: Optional[float], info: Dict[str, Any]) -> Optional[float]:
        """Validate discount value based on type."""
        if v is None:
            return v
        data = info.data
        discount_type = data.get('discount_type')
        if discount_type == CouponTypeEnum.PERCENTAGE and (v <= 0 or v > 100):
            raise ValueError('Percentage discount must be between 1 and 100')
        if discount_type == CouponTypeEnum.FIXED and v <= 0:
            raise ValueError('Fixed discount must be greater than 0')
        return v


# ============================================================
# COUPON APPLY SCHEMA (Public)
# ============================================================

class CouponApply(CouponBase):
    """Schema for applying a coupon."""
    
    code: str = Field(..., description="Coupon code")
    amount: float = Field(..., gt=0, description="Purchase amount")
    target_type: Optional[CouponTargetTypeEnum] = Field(
        default=CouponTargetTypeEnum.ALL,
        description="Target type"
    )
    target_id: Optional[int] = Field(default=None, gt=0, description="Target ID")
    user_id: Optional[int] = Field(default=None, gt=0, description="User ID (for validation)")


class CouponApplyResponse(CouponBase):
    """Schema for coupon apply response."""
    
    valid: bool = Field(..., description="Is coupon valid")
    message: str = Field(..., description="Validation message")
    discount_amount: float = Field(default=0, description="Discount amount")
    discounted_price: float = Field(default=0, description="Discounted price")
    coupon_id: Optional[int] = Field(default=None, description="Coupon ID")
    code: Optional[str] = Field(default=None, description="Coupon code")
    discount_type: Optional[str] = Field(default=None, description="Discount type")
    discount_value: Optional[float] = Field(default=None, description="Discount value")


# ============================================================
# COUPON RESPONSE SCHEMA
# ============================================================

class CouponResponse(CouponBase):
    """Schema for coupon response."""
    
    id: int = Field(..., description="Coupon ID")
    code: str = Field(..., description="Coupon code")
    description: Optional[str] = Field(default=None, description="Coupon description")
    
    discount_type: str = Field(..., description="Discount type")
    discount_value: float = Field(..., description="Discount value")
    discount_display: str = Field(..., description="Display discount")
    max_discount_amount: Optional[float] = Field(default=None, description="Maximum discount amount")
    min_purchase_amount: float = Field(..., description="Minimum purchase amount")
    
    target_type: str = Field(..., description="Target type")
    target_display: str = Field(..., description="Human-readable target")
    target_id: Optional[int] = Field(default=None, description="Target ID")
    
    usage_limit: Optional[int] = Field(default=None, description="Usage limit")
    used_count: int = Field(..., description="Used count")
    remaining_uses: int = Field(..., description="Remaining uses")
    has_unlimited_uses: bool = Field(..., description="Has unlimited uses")
    per_user_limit: int = Field(..., description="Per user limit")
    first_time_only: bool = Field(..., description="First-time only")
    
    status: str = Field(..., description="Coupon status")
    display_status: str = Field(..., description="Human-readable status")
    is_active: bool = Field(..., description="Is active")
    is_expired: bool = Field(..., description="Is expired")
    is_depleted: bool = Field(..., description="Is depleted")
    
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    days_until_expiry: int = Field(..., description="Days until expiry")
    days_since_start: int = Field(..., description="Days since start")
    usage_rate: float = Field(..., description="Usage rate percentage")
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# COUPON USAGE RESPONSE SCHEMA
# ============================================================

class CouponUsageResponse(CouponBase):
    """Schema for coupon usage response."""
    
    id: int = Field(..., description="Usage ID")
    coupon_id: int = Field(..., description="Coupon ID")
    coupon_code: str = Field(..., description="Coupon code")
    
    user_id: int = Field(..., description="User ID")
    user_name: Optional[str] = Field(default=None, description="User name")
    user_email: Optional[str] = Field(default=None, description="User email")
    
    enrollment_id: Optional[int] = Field(default=None, description="Enrollment ID")
    path_enrollment_id: Optional[int] = Field(default=None, description="Path enrollment ID")
    
    discount_applied: float = Field(..., description="Discount applied")
    original_amount: float = Field(..., description="Original amount")
    final_amount: float = Field(..., description="Final amount")
    savings_display: str = Field(..., description="Savings display")
    
    status: str = Field(..., description="Usage status")
    used_at: datetime = Field(..., description="Used at timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiry timestamp")
    cancelled_at: Optional[datetime] = Field(default=None, description="Cancelled timestamp")
    
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")


# ============================================================
# COUPON LIST REQUEST (Filters)
# ============================================================

class CouponListRequest(CouponBase):
    """Schema for coupon list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by code or description")
    status: Optional[CouponStatusEnum] = Field(default=None, description="Filter by status")
    discount_type: Optional[CouponTypeEnum] = Field(default=None, description="Filter by discount type")
    target_type: Optional[CouponTargetTypeEnum] = Field(default=None, description="Filter by target type")
    created_by: Optional[int] = Field(default=None, description="Filter by creator")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# COUPON LIST RESPONSE
# ============================================================

class CouponListResponse(CouponBase):
    """Schema for paginated coupon list response."""
    
    coupons: List[CouponResponse] = Field(..., description="List of coupons")
    total: int = Field(..., description="Total coupons")
    active_count: int = Field(..., description="Active coupons")
    expired_count: int = Field(..., description="Expired coupons")
    depleted_count: int = Field(..., description="Depleted coupons")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# COUPON STATISTICS (Admin View)
# ============================================================

class CouponStatistics(CouponBase):
    """Schema for coupon statistics."""
    
    total_coupons: int = Field(..., description="Total coupons")
    active: int = Field(..., description="Active coupons")
    inactive: int = Field(..., description="Inactive coupons")
    expired: int = Field(..., description="Expired coupons")
    depleted: int = Field(..., description="Depleted coupons")
    
    # NEW: Usage stats
    total_usages: int = Field(..., description="Total usages")
    total_discount_given: float = Field(..., description="Total discount given")
    average_discount: float = Field(..., description="Average discount")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Coupons by type"
    )
    
    # NEW: Most used coupons
    most_used: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most used coupons"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily usage trends"
    )


# ============================================================
# COUPON BULK CREATE SCHEMA
# ============================================================

class CouponBulkCreate(CouponBase):
    """Schema for bulk coupon creation."""
    
    codes: List[str] = Field(..., min_length=1, description="List of coupon codes")
    description: str = Field(..., min_length=3, max_length=500, description="Coupon description")
    
    discount_type: CouponTypeEnum = Field(..., description="Discount type")
    discount_value: float = Field(..., gt=0, description="Discount value")
    max_discount_amount: Optional[float] = Field(default=None, gt=0, description="Maximum discount amount")
    min_purchase_amount: float = Field(default=0, ge=0, description="Minimum purchase amount")
    
    target_type: CouponTargetTypeEnum = Field(
        default=CouponTargetTypeEnum.ALL,
        description="Target type"
    )
    target_id: Optional[int] = Field(default=None, gt=0, description="Target ID")
    
    usage_limit: Optional[int] = Field(default=None, gt=0, description="Usage limit")
    per_user_limit: int = Field(default=1, ge=1, description="Limit per user")
    first_time_only: bool = Field(default=False, description="First-time users only")
    
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    
    status: CouponStatusEnum = Field(
        default=CouponStatusEnum.ACTIVE,
        description="Coupon status"
    )


class CouponBulkResponse(CouponBase):
    """Schema for bulk coupon response."""
    
    success_count: int = Field(..., description="Number of successful coupon creations")
    failed_count: int = Field(..., description="Number of failed coupon creations")
    created_coupons: List[CouponResponse] = Field(
        default_factory=list,
        description="Created coupons"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CouponTypeEnum",
    "CouponStatusEnum",
    "CouponTargetTypeEnum",
    "CouponUsageStatusEnum",
    "CouponCreate",
    "CouponUpdate",
    "CouponApply",
    "CouponApplyResponse",
    "CouponResponse",
    "CouponUsageResponse",
    "CouponListRequest",
    "CouponListResponse",
    "CouponStatistics",
    "CouponBulkCreate",
    "CouponBulkResponse",
]