# ============================================================
# AETHER LINK - SESSION SCHEMAS (UPGRADED)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import re


# ============================================================
# SESSION ENUMS (UPGRADED)
# ============================================================

class SessionStatusEnum(str, Enum):
    """Session status enumeration for schemas."""
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionTypeEnum(str, Enum):  # NEW
    """Session type enumeration."""
    LECTURE = "lecture"
    LAB = "lab"
    QUIZ = "quiz"
    REVIEW = "review"
    WORKSHOP = "workshop"
    OFFICE_HOURS = "office_hours"
    OTHER = "other"


# ============================================================
# BASE SCHEMA
# ============================================================

class SessionBase(BaseModel):
    """Base session schema with common fields."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )
    
    session_number: int = Field(..., gt=0, description="Session number in course")
    title: str = Field(..., min_length=3, max_length=255, description="Session title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Session description")
    date_time: datetime = Field(..., description="Session date and time")
    duration_minutes: int = Field(default=60, ge=1, le=480, description="Duration in minutes (1-480)")
    
    # NEW: Session type
    session_type: SessionTypeEnum = Field(
        default=SessionTypeEnum.LECTURE,
        description="Session type"
    )
    
    # NEW: End time (calculated)
    end_time: Optional[datetime] = Field(default=None, description="Session end time")
    
    # NEW: Timezone
    timezone: str = Field(default="UTC", max_length=50, description="Session timezone")
    
    # Zoom Integration
    zoom_meeting_id: Optional[str] = Field(default=None, min_length=5, max_length=100, description="Zoom meeting ID")
    zoom_join_url: Optional[str] = Field(default=None, max_length=500, description="Zoom join URL")
    zoom_start_url: Optional[str] = Field(default=None, max_length=500, description="Zoom start URL")
    zoom_password: Optional[str] = Field(default=None, max_length=20, description="Zoom meeting password")
    
    # NEW: Zoom settings
    zoom_settings: Optional[Dict[str, Any]] = Field(default=None, description="Zoom meeting settings")
    
    # Recording
    recording_url: Optional[str] = Field(default=None, max_length=500, description="Recording URL")
    
    # NEW: Recording metadata
    recording_duration_minutes: Optional[int] = Field(default=None, ge=0, description="Recording duration")
    recording_file_size: Optional[int] = Field(default=None, ge=0, description="Recording file size in bytes")
    recording_mime_type: Optional[str] = Field(default=None, max_length=50, description="Recording MIME type")
    recording_download_url: Optional[str] = Field(default=None, max_length=500, description="Recording download URL")
    
    # NEW: Recording transcript
    recording_transcript: Optional[str] = Field(default=None, description="Recording transcript")
    recording_transcript_url: Optional[str] = Field(default=None, max_length=500, description="Transcript URL")
    
    # NEW: Live/Recorded flags
    is_live: bool = Field(default=True, description="Is this a live session?")
    is_recorded: bool = Field(default=False, description="Is this session recorded?")
    
    # Status
    status: SessionStatusEnum = Field(default=SessionStatusEnum.UPCOMING, description="Session status")
    
    meeting_notes: Optional[str] = Field(default=None, max_length=5000, description="Meeting notes")
    resources: Optional[Dict[str, Any]] = Field(default=None, description="Additional resources (JSON)")
    
    # NEW: Instructor notes (private)
    instructor_notes: Optional[str] = Field(default=None, max_length=5000, description="Instructor private notes")
    
    # NEW: Student instructions
    student_instructions: Optional[str] = Field(default=None, max_length=5000, description="Instructions for students")
    
    @field_validator('date_time')
    @classmethod
    def validate_date_time(cls, v: datetime) -> datetime:
        """Validate date_time is in the future."""
        if v < datetime.now(timezone.utc):
            raise ValueError('Date and time must be in the future')
        return v
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: Optional[datetime], info: Dict[str, Any]) -> Optional[datetime]:
        """Validate end time is after start time."""
        if v is None:
            return v
        data = info.data
        if 'date_time' in data and v <= data['date_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @field_validator('zoom_join_url')
    @classmethod
    def validate_zoom_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Zoom URL format."""
        if v is None or v == "":
            return v
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Zoom URL must be a valid URL')
        if 'zoom.us' not in v.lower():
            raise ValueError('Invalid Zoom URL')
        return v
    
    @field_validator('recording_url')
    @classmethod
    def validate_recording_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate recording URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Recording URL must be a valid URL')
        return v
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate duration is within limits."""
        if v < 1:
            raise ValueError('Duration must be at least 1 minute')
        if v > 480:
            raise ValueError('Duration must be less than 480 minutes (8 hours)')
        return v


# ============================================================
# SESSION CREATE SCHEMA
# ============================================================

class SessionCreate(SessionBase):
    """Schema for creating a session."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    
    # NEW: Auto-create Zoom meeting
    create_zoom_meeting: bool = Field(default=True, description="Auto-create Zoom meeting")
    
    # NEW: Auto-record
    auto_record: bool = Field(default=False, description="Auto-record session")


# ============================================================
# SESSION UPDATE SCHEMA
# ============================================================

class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )
    
    session_number: Optional[int] = Field(default=None, gt=0, description="Session number in course")
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Session title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Session description")
    date_time: Optional[datetime] = Field(default=None, description="Session date and time")
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=480, description="Duration in minutes (1-480)")
    
    # NEW: Session type
    session_type: Optional[SessionTypeEnum] = Field(default=None, description="Session type")
    
    # Zoom Integration
    zoom_meeting_id: Optional[str] = Field(default=None, min_length=5, max_length=100, description="Zoom meeting ID")
    zoom_join_url: Optional[str] = Field(default=None, max_length=500, description="Zoom join URL")
    zoom_start_url: Optional[str] = Field(default=None, max_length=500, description="Zoom start URL")
    zoom_password: Optional[str] = Field(default=None, max_length=20, description="Zoom meeting password")
    
    # Recording
    recording_url: Optional[str] = Field(default=None, max_length=500, description="Recording URL")
    recording_available: Optional[bool] = Field(default=None, description="Recording available?")
    recording_duration_minutes: Optional[int] = Field(default=None, ge=0, description="Recording duration")
    
    # NEW: Live/Recorded flags
    is_live: Optional[bool] = Field(default=None, description="Is this a live session?")
    is_recorded: Optional[bool] = Field(default=None, description="Is this session recorded?")
    
    # Status
    status: Optional[SessionStatusEnum] = Field(default=None, description="Session status")
    
    meeting_notes: Optional[str] = Field(default=None, max_length=5000, description="Meeting notes")
    resources: Optional[Dict[str, Any]] = Field(default=None, description="Additional resources (JSON)")
    
    # NEW: Instructor notes (private)
    instructor_notes: Optional[str] = Field(default=None, max_length=5000, description="Instructor private notes")
    student_instructions: Optional[str] = Field(default=None, max_length=5000, description="Instructions for students")
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        """Validate duration is within limits."""
        if v is not None:
            if v < 1:
                raise ValueError('Duration must be at least 1 minute')
            if v > 480:
                raise ValueError('Duration must be less than 480 minutes (8 hours)')
        return v


# ============================================================
# RECORDING ADD SCHEMA
# ============================================================

class RecordingAdd(BaseModel):
    """Schema for adding recording to a session."""
    model_config = ConfigDict(from_attributes=True)
    
    recording_url: str = Field(..., max_length=500, description="Recording URL")
    recording_available: bool = Field(default=True, description="Recording available?")
    
    # NEW: Recording metadata
    recording_duration_minutes: Optional[int] = Field(default=None, ge=0, description="Recording duration")
    recording_file_size: Optional[int] = Field(default=None, ge=0, description="Recording file size in bytes")
    recording_mime_type: Optional[str] = Field(default=None, max_length=50, description="Recording MIME type")
    recording_download_url: Optional[str] = Field(default=None, max_length=500, description="Recording download URL")
    
    # NEW: Recording transcript
    recording_transcript: Optional[str] = Field(default=None, description="Recording transcript")
    recording_transcript_url: Optional[str] = Field(default=None, max_length=500, description="Transcript URL")
    
    @field_validator('recording_url')
    @classmethod
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
    
    # NEW: Attendance statistics
    total_students: int = Field(default=0, description="Total students enrolled")
    present_count: int = Field(default=0, description="Present count")
    absent_count: int = Field(default=0, description="Absent count")
    made_up_count: int = Field(default=0, description="Made up count")
    attendance_percentage: int = Field(default=0, description="Attendance percentage")
    
    # NEW: Attendance summary
    attendance_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Attendance summary"
    )
    
    recording_available: bool = Field(default=False, description="Recording available?")
    recording_processed_at: Optional[datetime] = Field(default=None, description="Recording processed at")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# SESSION DETAIL RESPONSE
# ============================================================

class SessionDetailResponse(SessionResponse):
    """Schema for session detail response with course info."""
    
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    teacher_name: Optional[str] = Field(default=None, description="Teacher name")
    
    # NEW: Materials
    materials: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Session materials"
    )


# ============================================================
# SESSION LIST REQUEST (Filters)
# ============================================================

class SessionListRequest(BaseModel):
    """Schema for session list request with filters."""
    model_config = ConfigDict(from_attributes=True)
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title")
    status: Optional[SessionStatusEnum] = Field(default=None, description="Filter by status")
    session_type: Optional[SessionTypeEnum] = Field(default=None, description="Filter by session type")
    is_live: Optional[bool] = Field(default=None, description="Filter by live sessions")
    has_recording: Optional[bool] = Field(default=None, description="Filter by recording availability")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="date_time", description="Sort field")
    sort_order: str = Field(default="asc", description="Sort order (asc/desc)")


# ============================================================
# SESSION LIST RESPONSE
# ============================================================

class SessionListResponse(BaseModel):
    """Schema for paginated session list response."""
    model_config = ConfigDict(from_attributes=True)
    
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# SESSION STATISTICS (NEW)
# ============================================================

class SessionStatistics(BaseModel):
    """Schema for session statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_sessions: int = Field(..., description="Total sessions")
    upcoming: int = Field(..., description="Upcoming sessions")
    live: int = Field(..., description="Live sessions")
    completed: int = Field(..., description="Completed sessions")
    cancelled: int = Field(..., description="Cancelled sessions")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Sessions by type"
    )
    
    # NEW: Recording stats
    sessions_with_recording: int = Field(..., description="Sessions with recording")
    sessions_without_recording: int = Field(..., description="Sessions without recording")
    
    # NEW: Attendance stats
    total_attendance_records: int = Field(..., description="Total attendance records")
    average_attendance_rate: float = Field(..., description="Average attendance rate")
    
    # NEW: Upcoming sessions
    upcoming_sessions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Upcoming sessions list"
    )


# ============================================================
# SESSION ZOOM SYNC (NEW)
# ============================================================

class SessionZoomSync(BaseModel):
    """Schema for syncing Zoom meeting data."""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: int = Field(..., gt=0, description="Session ID")
    sync_attendance: bool = Field(default=True, description="Sync attendance data from Zoom")


class SessionZoomSyncResponse(BaseModel):
    """Schema for Zoom sync response."""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(..., description="Sync success")
    message: str = Field(..., description="Sync message")
    attendees_synced: int = Field(default=0, description="Number of attendees synced")
    attendance_updated: int = Field(default=0, description="Number of attendance records updated")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SessionStatusEnum",
    "SessionTypeEnum",
    "SessionBase",
    "SessionCreate",
    "SessionUpdate",
    "RecordingAdd",
    "SessionResponse",
    "SessionDetailResponse",
    "SessionListRequest",
    "SessionListResponse",
    "SessionStatistics",
    "SessionZoomSync",
    "SessionZoomSyncResponse",
]