# ============================================================
# AETHER LINK - MATERIAL SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# MATERIAL TYPE ENUM
# ============================================================

class MaterialTypeEnum(str, Enum):
    """Material type enumeration for schemas."""
    PDF = "pdf"
    PPTX = "pptx"
    DOC = "doc"
    DOCX = "docx"
    LINK = "link"
    TXT = "txt"  # Added for testing


# ============================================================
# MATERIAL UPLOAD SCHEMA
# ============================================================

class MaterialUpload(BaseModel):
    """Schema for uploading course material."""

    title: str = Field(..., min_length=3, max_length=255, description="Material title")
    description: Optional[str] = Field(None, max_length=1000, description="Material description")

    # File or Link
    file_type: MaterialTypeEnum = Field(..., description="Material type")
    file_url: Optional[str] = Field(None, max_length=500, description="File URL (for files)")
    file_name: Optional[str] = Field(None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")

    # Link (if type is LINK)
    link_url: Optional[str] = Field(None, max_length=500, description="Link URL (for links)")

    course_id: int = Field(..., gt=0, description="Course ID")

    @validator('file_type')
    def validate_file_type(cls, v: MaterialTypeEnum) -> MaterialTypeEnum:
        """Validate file type."""
        allowed = [
            MaterialTypeEnum.PDF, 
            MaterialTypeEnum.PPTX, 
            MaterialTypeEnum.DOC, 
            MaterialTypeEnum.DOCX, 
            MaterialTypeEnum.LINK,
            MaterialTypeEnum.TXT
        ]
        if v not in allowed:
            raise ValueError(f'Invalid file type. Allowed: {[m.value for m in allowed]}')
        return v

    @validator('link_url')
    def validate_link_url(cls, v: Optional[str], values: dict) -> Optional[str]:
        """Validate link URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Link URL must be a valid URL')
        return v

    @validator('file_size')
    def validate_file_size(cls, v: Optional[int]) -> Optional[int]:
        """Validate file size (max 20 MB)."""
        if v is None:
            return v
        max_size = 20 * 1024 * 1024  # 20 MB
        if v > max_size:
            raise ValueError(f'File size must be less than {max_size / (1024 * 1024):.0f} MB')
        return v

    @validator('link_url', always=True)
    def validate_link_required(cls, v: Optional[str], values: dict) -> Optional[str]:
        """Validate link_url is provided when file_type is LINK."""
        file_type = values.get('file_type')
        if file_type == MaterialTypeEnum.LINK and not v:
            raise ValueError('Link URL is required for link type')
        return v


# ============================================================
# MATERIAL UPDATE SCHEMA
# ============================================================

class MaterialUpdate(BaseModel):
    """Schema for updating course material."""

    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Material title")
    description: Optional[str] = Field(None, max_length=1000, description="Material description")
    is_published: Optional[bool] = Field(None, description="Is material published?")

    # File updates
    file_url: Optional[str] = Field(None, max_length=500, description="File URL")
    file_name: Optional[str] = Field(None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")

    # Link updates
    link_url: Optional[str] = Field(None, max_length=500, description="Link URL")

    @validator('link_url')
    def validate_link_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate link URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Link URL must be a valid URL')
        return v


# ============================================================
# MATERIAL RESPONSE SCHEMA
# ============================================================

class MaterialResponse(BaseModel):
    """Schema for material response."""

    id: int = Field(..., description="Material ID")
    course_id: int = Field(..., description="Course ID")

    title: str = Field(..., description="Material title")
    description: Optional[str] = Field(None, description="Material description")

    file_type: MaterialTypeEnum = Field(..., description="Material type")
    file_url: Optional[str] = Field(None, description="File URL")
    file_name: Optional[str] = Field(None, description="Original file name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")

    is_link: bool = Field(False, description="Is this a link?")
    link_url: Optional[str] = Field(None, description="Link URL")

    is_published: bool = Field(True, description="Is material published?")

    uploaded_by: int = Field(..., description="Uploader ID")
    uploaded_by_name: Optional[str] = Field(None, description="Uploader name")

    size_mb: Optional[float] = Field(None, description="File size in MB")
    storage_path: Optional[str] = Field(None, description="Storage path in Supabase")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


# ============================================================
# MATERIAL LIST RESPONSE
# ============================================================

class MaterialListResponse(BaseModel):
    """Schema for paginated material list response."""

    materials: List[MaterialResponse] = Field(..., description="List of materials")
    total: int = Field(..., description="Total number of materials")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "MaterialTypeEnum",
    "MaterialUpload",
    "MaterialUpdate",
    "MaterialResponse",
    "MaterialListResponse",
]