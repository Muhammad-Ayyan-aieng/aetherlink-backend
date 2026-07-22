# ============================================================
# AETHER LINK - MATERIAL SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# MATERIAL ENUMS (UPGRADED)
# ============================================================

class MaterialTypeEnum(str, Enum):
    """Material type enumeration for schemas."""
    PDF = "pdf"
    PPTX = "pptx"
    DOC = "doc"
    DOCX = "docx"
    VIDEO = "video"          # NEW
    AUDIO = "audio"          # NEW
    IMAGE = "image"          # NEW
    LINK = "link"
    YOUTUBE = "youtube"      # NEW
    VIMEO = "vimeo"          # NEW
    ZOOM = "zoom"            # NEW
    TEXT = "text"            # NEW
    OTHER = "other"          # NEW


class MaterialVisibilityEnum(str, Enum):  # NEW
    """Material visibility enumeration."""
    PUBLIC = "public"
    ENROLLED_ONLY = "enrolled_only"
    TEACHER_ONLY = "teacher_only"
    ADMIN_ONLY = "admin_only"


# ============================================================
# BASE SCHEMA
# ============================================================

class MaterialBase(BaseModel):
    """Base material schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# MATERIAL UPLOAD SCHEMA
# ============================================================

class MaterialUpload(MaterialBase):
    """Schema for uploading course material."""

    title: str = Field(..., min_length=3, max_length=255, description="Material title")
    description: Optional[str] = Field(default=None, max_length=1000, description="Material description")
    
    # NEW: Session association
    session_id: Optional[int] = Field(default=None, gt=0, description="Session ID to link material to")

    # File or Link
    material_type: MaterialTypeEnum = Field(..., description="Material type")
    
    # File fields
    file_url: Optional[str] = Field(default=None, max_length=500, description="File URL (for files)")
    file_name: Optional[str] = Field(default=None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, max_length=100, description="MIME type")
    
    # Storage path (for Supabase)
    storage_path: Optional[str] = Field(default=None, max_length=500, description="Storage path in Supabase")

    # Link fields
    link_url: Optional[str] = Field(default=None, max_length=500, description="Link URL (for links)")
    
    # NEW: Video specific fields
    video_duration_seconds: Optional[int] = Field(default=None, ge=0, description="Video duration in seconds")
    video_thumbnail_url: Optional[str] = Field(default=None, max_length=500, description="Video thumbnail URL")
    video_platform: Optional[str] = Field(default=None, max_length=50, description="Video platform (youtube, vimeo, custom)")
    
    # NEW: Is this a recording?
    is_recording: bool = Field(default=False, description="Is this a session recording?")
    
    # NEW: Visibility
    visibility: MaterialVisibilityEnum = Field(
        default=MaterialVisibilityEnum.ENROLLED_ONLY,
        description="Material visibility"
    )
    
    course_id: int = Field(..., gt=0, description="Course ID")
    
    @field_validator('link_url')
    @classmethod
    def validate_link_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate link URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Link URL must be a valid URL')
        return v
    
    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: Optional[int]) -> Optional[int]:
        """Validate file size (max 200 MB for videos, 20 MB for documents)."""
        if v is None:
            return v
        # 200 MB for videos, 20 MB for documents
        max_size = 200 * 1024 * 1024  # 200 MB
        if v > max_size:
            raise ValueError(f'File size must be less than {max_size / (1024 * 1024):.0f} MB')
        return v


# ============================================================
# MATERIAL UPDATE SCHEMA
# ============================================================

class MaterialUpdate(MaterialBase):
    """Schema for updating course material."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Material title")
    description: Optional[str] = Field(default=None, max_length=1000, description="Material description")
    
    # NEW: Session association
    session_id: Optional[int] = Field(default=None, gt=0, description="Session ID to link material to")
    
    is_published: Optional[bool] = Field(default=None, description="Is material published?")
    
    # NEW: Visibility
    visibility: Optional[MaterialVisibilityEnum] = Field(default=None, description="Material visibility")

    # File updates
    file_url: Optional[str] = Field(default=None, max_length=500, description="File URL")
    file_name: Optional[str] = Field(default=None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")

    # Link updates
    link_url: Optional[str] = Field(default=None, max_length=500, description="Link URL")
    
    # NEW: Video specific fields
    video_duration_seconds: Optional[int] = Field(default=None, ge=0, description="Video duration in seconds")
    video_thumbnail_url: Optional[str] = Field(default=None, max_length=500, description="Video thumbnail URL")

    @field_validator('link_url')
    @classmethod
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

class MaterialResponse(MaterialBase):
    """Schema for material response."""

    id: int = Field(..., description="Material ID")
    course_id: int = Field(..., description="Course ID")
    
    # NEW: Session association
    session_id: Optional[int] = Field(default=None, description="Session ID")
    session_title: Optional[str] = Field(default=None, description="Session title")

    title: str = Field(..., description="Material title")
    description: Optional[str] = Field(default=None, description="Material description")
    
    # NEW: Display type
    material_type: str = Field(..., description="Material type")
    display_type: str = Field(..., description="Human-readable material type")
    icon_class: str = Field(..., description="Icon class for UI")

    file_url: Optional[str] = Field(default=None, description="File URL")
    file_name: Optional[str] = Field(default=None, description="Original file name")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    
    # NEW: Storage info
    storage_path: Optional[str] = Field(default=None, description="Storage path in Supabase")
    storage_bucket: Optional[str] = Field(default=None, description="Storage bucket name")

    is_link: bool = Field(default=False, description="Is this a link?")
    link_url: Optional[str] = Field(default=None, description="Link URL")
    
    # NEW: Video specific fields
    video_duration_seconds: Optional[int] = Field(default=None, description="Video duration in seconds")
    video_thumbnail_url: Optional[str] = Field(default=None, description="Video thumbnail URL")
    video_platform: Optional[str] = Field(default=None, description="Video platform")
    
    # NEW: Recording info
    is_recording: bool = Field(default=False, description="Is this a session recording?")
    recording_session_id: Optional[int] = Field(default=None, description="Session ID this is a recording of")

    is_published: bool = Field(default=True, description="Is material published?")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    
    # NEW: Visibility
    visibility: str = Field(default="enrolled_only", description="Material visibility")
    is_public: bool = Field(default=False, description="Is material public?")
    is_enrolled_only: bool = Field(default=True, description="Is material for enrolled students only?")

    uploaded_by: int = Field(..., description="Uploader ID")
    uploaded_by_name: Optional[str] = Field(default=None, description="Uploader name")
    
    # NEW: Last editor
    last_edited_by: Optional[int] = Field(default=None, description="Last editor ID")
    last_edited_by_name: Optional[str] = Field(default=None, description="Last editor name")

    # NEW: Statistics
    view_count: int = Field(default=0, description="Number of views")
    download_count: int = Field(default=0, description="Number of downloads")
    last_viewed_at: Optional[datetime] = Field(default=None, description="Last view timestamp")
    last_downloaded_at: Optional[datetime] = Field(default=None, description="Last download timestamp")
    
    size_mb: Optional[float] = Field(default=None, description="File size in MB")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# MATERIAL LIST REQUEST (Filters)
# ============================================================

class MaterialListRequest(MaterialBase):
    """Schema for material list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title")
    material_type: Optional[MaterialTypeEnum] = Field(default=None, description="Filter by type")
    visibility: Optional[MaterialVisibilityEnum] = Field(default=None, description="Filter by visibility")
    is_published: Optional[bool] = Field(default=None, description="Filter by published status")
    is_recording: Optional[bool] = Field(default=None, description="Filter by recording")
    session_id: Optional[int] = Field(default=None, description="Filter by session")
    uploaded_by: Optional[int] = Field(default=None, description="Filter by uploader")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# MATERIAL LIST RESPONSE
# ============================================================

class MaterialListResponse(MaterialBase):
    """Schema for paginated material list response."""

    materials: List[MaterialResponse] = Field(..., description="List of materials")
    total: int = Field(..., description="Total number of materials")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# MATERIAL BULK OPERATION
# ============================================================

class MaterialBulkOperation(MaterialBase):
    """Schema for bulk material operations."""
    
    material_ids: List[int] = Field(..., description="List of material IDs")
    action: str = Field(..., description="Action to perform (publish, unpublish, delete)")
    note: Optional[str] = Field(default=None, description="Operation note")


# ============================================================
# MATERIAL STATISTICS
# ============================================================

class MaterialStatistics(MaterialBase):
    """Schema for material statistics."""
    
    total_materials: int = Field(..., description="Total materials")
    total_files: int = Field(..., description="Total files")
    total_links: int = Field(..., description="Total links")
    total_videos: int = Field(..., description="Total videos")
    total_views: int = Field(..., description="Total views")
    total_downloads: int = Field(..., description="Total downloads")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Materials by type"
    )
    
    # NEW: By visibility
    visibility_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Materials by visibility"
    )
    
    # NEW: Most viewed
    most_viewed: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most viewed materials"
    )
    
    # NEW: Most downloaded
    most_downloaded: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most downloaded materials"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "MaterialTypeEnum",
    "MaterialVisibilityEnum",
    "MaterialUpload",
    "MaterialUpdate",
    "MaterialResponse",
    "MaterialListRequest",
    "MaterialListResponse",
    "MaterialBulkOperation",
    "MaterialStatistics",
]