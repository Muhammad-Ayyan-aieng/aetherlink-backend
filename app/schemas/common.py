# ============================================================
# AETHER LINK - COMMON SCHEMAS
# ============================================================
# Shared schemas for pagination, responses, and base models
# ============================================================

from typing import Optional, Generic, TypeVar, List, Any, Dict
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from enum import Enum


# ============================================================
# GENERIC TYPES
# ============================================================

T = TypeVar('T')


# ============================================================
# BASE SCHEMAS
# ============================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


class BaseResponse(BaseSchema):
    """Base response schema."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# PAGINATION SCHEMAS
# ============================================================

class PaginationParams(BaseSchema):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")
    search: Optional[str] = Field(default=None, description="Search query")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total items count")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    pages: int = Field(description="Total pages")
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        """Create paginated response."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )


# ============================================================
# STANDARD RESPONSE WRAPPERS
# ============================================================

class StandardResponse(BaseSchema, Generic[T]):
    """Standard API response wrapper."""
    success: bool = Field(default=True)
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[Dict[str, Any]]] = None


class ErrorResponse(BaseSchema):
    """Error response schema."""
    success: bool = Field(default=False)
    error: Dict[str, Any] = Field(description="Error details")
    message: Optional[str] = None
    details: Optional[Any] = None


# ============================================================
# ID SCHEMAS
# ============================================================

class IDSchema(BaseSchema):
    """Schema for ID-based operations."""
    id: int = Field(..., description="Resource ID")


class IDsSchema(BaseSchema):
    """Schema for multiple IDs."""
    ids: List[int] = Field(..., description="List of resource IDs")


# ============================================================
# DATE RANGE SCHEMAS
# ============================================================

class DateRange(BaseSchema):
    """Date range filter."""
    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")


class DateTimeRange(BaseSchema):
    """DateTime range filter."""
    start_at: Optional[datetime] = Field(default=None, description="Start datetime")
    end_at: Optional[datetime] = Field(default=None, description="End datetime")


# ============================================================
# ENUM SCHEMAS
# ============================================================

class EnumSchema(BaseSchema):
    """Schema for enum values."""
    value: str
    label: str


class EnumListResponse(BaseSchema):
    """Response for list of enums."""
    enums: List[EnumSchema]


# ============================================================
# BULK OPERATIONS
# ============================================================

class BulkOperationResponse(BaseSchema):
    """Response for bulk operations."""
    success_count: int = Field(description="Number of successful operations")
    failed_count: int = Field(description="Number of failed operations")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


# ============================================================
# HEALTH CHECK
# ============================================================

class HealthCheckResponse(BaseSchema):
    """Health check response."""
    status: str = Field(description="Status (healthy/unhealthy)")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    environment: str = Field(description="Environment")
    timestamp: datetime = Field(description="Current timestamp")
    database: str = Field(description="Database status")
    redis: str = Field(description="Redis status")