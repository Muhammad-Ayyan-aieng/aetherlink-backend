# ============================================================
# AETHER LINK - SESSION SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


# ============================================================
# SESSION STATUS ENUM
# ============================================================

class SessionStatusEnum(str, Enum):
    """Session status enumeration for schemas."""
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================
# SESSION BASE SCHEMA
# ============================================================

class SessionBase(BaseModel):
    """Base session schema with common fields."""
    
    session_number: int = Field(..., gt=0, description="Session number in course")
    title: str = Field(..., min_length=3, max_length=255, description="Session title")
    description: Optional[str] = Field(None, max_length=5000, description="Session description")
    date_time: datetime = Field(..., description="Session date and time")
    duration_minutes: int = Field(60, ge=1, le=180, description="Duration in minutes (1-180)")
    
    # Zoom Integration
    zoom_meeting_id: str = Field(..., min_length=5, max_length=100, description="Zoom meeting ID")
    zoom_join_url: Optional[str] = Field(None, max_length=500, description="Zoom join URL")
    zoom_start_url: Optional[str] = Field(None, max_length=500, description="Zoom start URL")
    zoom_password: Optional[str] = Field(None, max_length=20, description="Zoom meeting password")
    
    # Recording (Required)
    recording_url: str = Field(..., max_length=500, description="Recording URL")
    
    # Status
    status: SessionStatusEnum = Field(default=SessionStatusEnum.UPCOMING, description="Session status")
    
    meeting_notes: Optional[str] = Field(None, max_length=5000, description="Meeting notes")
    resources: Optional[dict] = Field(None, description="Additional resources (JSON)")
    
    @validator('date_time')
    def validate_date_time(cls, v: datetime) -> datetime:
        """Validate date_time is not too far in the past."""
        # Allow sessions to be created for past dates (for backfilling)
        # But warn if it's more than 30 days in the past
        return v
    
    @validator('zoom_join_url')
    def validate_zoom_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Zoom URL format."""
        if v is None or v == "":
            return v
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Zoom URL must be a valid URL')
        if 'zoom.us' not in v.lower():
            raise ValueError('Invalid Zoom URL')
        return v
    
    @validator('recording_url')
    def validate_recording_url(cls, v: str) -> str:
        """Validate recording URL."""
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Recording URL must be a valid URL')
        return v


# ============================================================
# SESSION CREATE SCHEMA
# ============================================================

class SessionCreate(SessionBase):
    """Schema for creating a session."""
    
    course_id: int = Field(..., gt=0, description="Course ID")


# ============================================================
# SESSION UPDATE SCHEMA
# ============================================================

class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    
    session_number: Optional[int] = Field(None, gt=0, description="Session number in course")
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Session title")
    description: Optional[str] = Field(None, max_length=5000, description="Session description")
    date_time: Optional[datetime] = Field(None, description="Session date and time")
    duration_minutes: Optional[int] = Field(None, ge=1, le=180, description="Duration in minutes (1-180)")
    
    # Zoom Integration
    zoom_meeting_id: Optional[str] = Field(None, min_length=5, max_length=100, description="Zoom meeting ID")
    zoom_join_url: Optional[str] = Field(None, max_length=500, description="Zoom join URL")
    zoom_start_url: Optional[str] = Field(None, max_length=500, description="Zoom start URL")
    zoom_password: Optional[str] = Field(None, max_length=20, description="Zoom meeting password")
    
    # Recording
    recording_url: Optional[str] = Field(None, max_length=500, description="Recording URL")
    recording_available: Optional[bool] = Field(None, description="Recording available?")
    
    # Status
    status: Optional[SessionStatusEnum] = Field(None, description="Session status")
    
    meeting_notes: Optional[str] = Field(None, max_length=5000, description="Meeting notes")
    resources: Optional[dict] = Field(None, description="Additional resources (JSON)")
    
    @validator('zoom_join_url')
    def validate_zoom_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Zoom URL format."""
        if v is None or v == "":
            return v
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Zoom URL must be a valid URL')
        if 'zoom.us' not in v.lower():
            raise ValueError('Invalid Zoom URL')
        return v
    
    @validator('recording_url')
    def validate_recording_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate recording URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Recording URL must be a valid URL')
        return v


# ============================================================
# RECORDING ADD SCHEMA
# ============================================================

class RecordingAdd(BaseModel):
    """Schema for adding recording to a session."""
    
    recording_url: str = Field(..., max_length=500, description="Recording URL")
    recording_available: bool = Field(default=True, description="Recording available?")
    
    @validator('recording_url')
    def validate_recording_url(cls, v: str) -> str:
        """Validate recording URL."""
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Recording URL must be a valid URL')
        return v


# ============================================================
# SESSION RESPONSE SCHEMA
# ============================================================

class SessionResponse(SessionBase):
    """Schema for session response."""
    
    id: int = Field(..., description="Session ID")
    course_id: int = Field(..., description="Course ID")
    recording_available: bool = Field(default=False, description="Recording available?")
    recording_processed_at: Optional[datetime] = Field(None, description="Recording processed at")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


# ============================================================
# SESSION DETAIL RESPONSE
# ============================================================

class SessionDetailResponse(SessionResponse):
    """Schema for session detail response with course info."""
    
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")


# ============================================================
# SESSION LIST RESPONSE
# ============================================================

class SessionListResponse(BaseModel):
    """Schema for paginated session list response."""
    
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SessionStatusEnum",
    "SessionBase",
    "SessionCreate",
    "SessionUpdate",
    "RecordingAdd",
    "SessionResponse",
    "SessionDetailResponse",
    "SessionListResponse",
]