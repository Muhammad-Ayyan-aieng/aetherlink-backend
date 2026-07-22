# ============================================================
# AETHER LINK - ATTENDANCE SCHEMAS ⭐ CRITICAL
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# ATTENDANCE STATUS ENUM (UPGRADED)
# ============================================================

class AttendanceStatusEnum(str, Enum):
    """Attendance status enumeration for schemas."""
    PRESENT = "present"
    MISSED = "missed"
    MADE_UP = "made_up"
    EXCUSED = "excused"
    LATE = "late"        # NEW
    PARTIAL = "partial"  # NEW


class MarkedByEnum(str, Enum):  # NEW
    """Who marked the attendance."""
    SYSTEM = "system"
    TEACHER = "teacher"
    ADMIN = "admin"
    ZOOM_API = "zoom_api"
    VIDEO_AUTO = "video_auto"


# ============================================================
# BASE SCHEMA
# ============================================================

class AttendanceBase(BaseModel):
    """Base attendance schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# ATTENDANCE MARK SCHEMA (Teacher/Admin)
# ============================================================

class AttendanceMark(AttendanceBase):
    """Schema for marking student attendance."""
    
    enrollment_id: int = Field(..., gt=0, description="Enrollment ID")
    session_id: int = Field(..., gt=0, description="Session ID")
    status: AttendanceStatusEnum = Field(..., description="Attendance status")
    remarks: Optional[str] = Field(default=None, max_length=500, description="Teacher remarks")
    
    # NEW: For late/partial tracking
    late_minutes: Optional[int] = Field(default=0, ge=0, le=180, description="Minutes late (for LATE status)")
    attended_minutes: Optional[int] = Field(default=None, ge=0, description="Minutes attended (for PARTIAL status)")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: AttendanceStatusEnum) -> AttendanceStatusEnum:
        """Validate status."""
        if v == AttendanceStatusEnum.MADE_UP:
            raise ValueError('Cannot mark as made_up directly. Use watch recording endpoint.')
        return v


# ============================================================
# ATTENDANCE UPDATE SCHEMA
# ============================================================

class AttendanceUpdate(AttendanceBase):
    """Schema for updating attendance record."""
    
    status: Optional[AttendanceStatusEnum] = Field(default=None, description="Attendance status")
    remarks: Optional[str] = Field(default=None, max_length=500, description="Remarks")
    verified: Optional[bool] = Field(default=None, description="Verify attendance")
    late_minutes: Optional[int] = Field(default=None, ge=0, le=180, description="Minutes late")
    
    # NEW: Makeup verification
    verify_makeup: Optional[bool] = Field(default=None, description="Verify makeup attendance")


# ============================================================
# WATCH RECORDING SCHEMA ⭐ CRITICAL (80% RULE)
# ============================================================

class WatchRecording(AttendanceBase):
    """Schema for student watching a recording."""
    
    watched_percentage: int = Field(..., ge=0, le=100, description="Percentage of recording watched (0-100)")
    
    # NEW: Watch metadata
    watch_duration_seconds: Optional[int] = Field(default=None, ge=0, description="Duration watched in seconds")
    device_type: Optional[str] = Field(default=None, max_length=50, description="Device type (mobile, desktop, tablet)")
    playback_speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Playback speed")
    
    @field_validator('watched_percentage')
    @classmethod
    def validate_percentage(cls, v: int) -> int:
        """Ensure percentage is between 0 and 100."""
        if v < 0:
            return 0
        if v > 100:
            return 100
        return v


# ============================================================
# ZOOM ATTENDANCE SYNC SCHEMA (NEW)
# ============================================================

class ZoomAttendanceSync(AttendanceBase):
    """Schema for syncing Zoom attendance data."""
    
    session_id: int = Field(..., gt=0, description="Session ID")
    participant_emails: List[str] = Field(..., description="List of participant emails from Zoom")
    sync_automatically: bool = Field(default=True, description="Auto-mark attendance based on 60% rule")


class ZoomAttendanceData(AttendanceBase):
    """Schema for Zoom attendance data."""
    
    email: str = Field(..., description="Participant email")
    name: str = Field(..., description="Participant name")
    join_time: datetime = Field(..., description="Join time")
    leave_time: Optional[datetime] = Field(default=None, description="Leave time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    attendance_percentage: float = Field(..., description="Attendance percentage")
    status: AttendanceStatusEnum = Field(..., description="Determined status")


# ============================================================
# ATTENDANCE RESPONSE SCHEMA
# ============================================================

class AttendanceResponse(AttendanceBase):
    """Schema for attendance record response."""
    
    id: int = Field(..., description="Attendance ID")
    enrollment_id: int = Field(..., description="Enrollment ID")
    session_id: int = Field(..., description="Session ID")
    status: AttendanceStatusEnum = Field(..., description="Attendance status")
    
    # NEW: Duration tracking
    duration_attended_minutes: int = Field(default=0, description="Minutes attended")
    total_session_minutes: int = Field(default=0, description="Total session minutes")
    attendance_percentage: float = Field(default=0.0, description="Attendance percentage")
    
    watched_recording: bool = Field(default=False, description="Watched recording?")
    watched_percentage: int = Field(default=0, description="Watched percentage (0-100)")
    last_watch_time: Optional[datetime] = Field(default=None, description="Last watch time")
    
    # NEW: Watch details
    total_watch_time_seconds: int = Field(default=0, description="Total watch time in seconds")
    watch_completed_at: Optional[datetime] = Field(default=None, description="Watch completion time")
    watch_device: Optional[str] = Field(default=None, description="Device used for watching")
    
    # NEW: Marked by
    marked_by: str = Field(default="system", description="Who marked attendance")
    marked_at: datetime = Field(..., description="When marked")
    marked_by_teacher_id: Optional[int] = Field(default=None, description="Teacher who marked")
    
    made_up_at: Optional[datetime] = Field(default=None, description="Made up timestamp")
    makeup_method: Optional[str] = Field(default=None, description="Makeup method")
    makeup_notes: Optional[str] = Field(default=None, description="Makeup notes")
    
    # NEW: Makeup verification
    makeup_reason: Optional[str] = Field(default=None, description="Makeup reason")
    makeup_verified_by: Optional[int] = Field(default=None, description="Makeup verified by")
    makeup_verified_at: Optional[datetime] = Field(default=None, description="Makeup verification time")
    
    # NEW: Late tracking
    late_minutes: int = Field(default=0, description="Minutes late")
    late_reason: Optional[str] = Field(default=None, description="Late reason")
    late_approved_by: Optional[int] = Field(default=None, description="Late approved by")
    late_approved_at: Optional[datetime] = Field(default=None, description="Late approval time")
    
    verified_by: Optional[int] = Field(default=None, description="Verified by (admin ID)")
    verified_at: Optional[datetime] = Field(default=None, description="Verification timestamp")
    remarks: Optional[str] = Field(default=None, description="Remarks")
    
    # NEW: Zoom data
    zoom_attendance_data: Optional[Dict[str, Any]] = Field(default=None, description="Raw Zoom attendance data")
    zoom_sync_at: Optional[datetime] = Field(default=None, description="Zoom sync timestamp")
    zoom_sync_status: Optional[str] = Field(default=None, description="Zoom sync status")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# MISSED SESSION RESPONSE ⭐ CRITICAL (Dashboard)
# ============================================================

class MissedSessionResponse(AttendanceBase):
    """Schema for missed session on student dashboard."""
    
    session_id: int = Field(..., description="Session ID")
    session_number: int = Field(..., description="Session number")
    session_title: str = Field(..., description="Session title")
    session_date: datetime = Field(..., description="Session date")
    
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    
    recording_url: Optional[str] = Field(default=None, description="Recording URL")
    recording_available: bool = Field(default=False, description="Recording available?")
    can_makeup: bool = Field(default=False, description="Can make up?")
    
    watched_percentage: int = Field(default=0, description="Watched percentage")
    days_ago: int = Field(..., description="Days since session")
    status: AttendanceStatusEnum = Field(..., description="Current status")
    
    # NEW: Makeup info
    makeup_method: Optional[str] = Field(default=None, description="How to make up")
    makeup_deadline: Optional[datetime] = Field(default=None, description="Makeup deadline")


# ============================================================
# ATTENDANCE SUMMARY SCHEMA (Student Dashboard)
# ============================================================

class AttendanceSummary(AttendanceBase):
    """Schema for student attendance summary."""
    
    student_id: int = Field(..., description="Student ID")
    course_id: Optional[int] = Field(default=None, description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    
    total_sessions: int = Field(default=0, description="Total sessions")
    present: int = Field(default=0, description="Present sessions")
    missed: int = Field(default=0, description="Missed sessions")
    made_up: int = Field(default=0, description="Made up sessions")
    excused: int = Field(default=0, description="Excused sessions")
    late: int = Field(default=0, description="Late sessions")
    partial: int = Field(default=0, description="Partial sessions")
    
    attended: int = Field(default=0, description="Attended sessions (present + made_up)")
    attendance_percentage: float = Field(default=0.0, description="Attendance percentage")
    
    missed_count: int = Field(default=0, description="Missed sessions count")
    missed_can_be_made_up: bool = Field(default=False, description="Can any missed sessions be made up?")
    
    # NEW: Engagement metrics
    total_watch_time_seconds: int = Field(default=0, description="Total video watch time")
    average_watch_percentage: float = Field(default=0.0, description="Average watch percentage")


# ============================================================
# COURSE ATTENDANCE SUMMARY (Teacher View)
# ============================================================

class StudentAttendanceSummary(AttendanceBase):
    """Schema for per-student attendance summary (teacher view)."""
    
    student_id: int = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    student_email: str = Field(..., description="Student email")
    student_avatar: Optional[str] = Field(default=None, description="Student avatar URL")
    
    total_sessions: int = Field(..., description="Total sessions")
    present: int = Field(..., description="Present sessions")
    missed: int = Field(..., description="Missed sessions")
    made_up: int = Field(..., description="Made up sessions")
    excused: int = Field(..., description="Excused sessions")
    late: int = Field(default=0, description="Late sessions")
    partial: int = Field(default=0, description="Partial sessions")
    attendance_percentage: float = Field(..., description="Attendance percentage")
    
    # NEW: Session details
    sessions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Detailed session attendance"
    )


class CourseAttendanceResponse(AttendanceBase):
    """Schema for course attendance report."""
    
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    total_students: int = Field(..., description="Total students in course")
    overall_attendance_rate: float = Field(..., description="Overall attendance rate")
    students: List[StudentAttendanceSummary] = Field(..., description="Student attendance data")


# ============================================================
# ATTENDANCE LIST REQUEST (Filters)
# ============================================================

class AttendanceListRequest(AttendanceBase):
    """Schema for attendance list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    enrollment_id: Optional[int] = Field(default=None, description="Filter by enrollment")
    session_id: Optional[int] = Field(default=None, description="Filter by session")
    status: Optional[AttendanceStatusEnum] = Field(default=None, description="Filter by status")
    marked_by: Optional[MarkedByEnum] = Field(default=None, description="Filter by who marked")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# ATTENDANCE LIST RESPONSE
# ============================================================

class AttendanceListResponse(AttendanceBase):
    """Schema for paginated attendance list response."""
    
    attendances: List[AttendanceResponse] = Field(..., description="List of attendance records")
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# ATTENDANCE STATISTICS (Admin View)
# ============================================================

class AttendanceStatistics(AttendanceBase):
    """Schema for platform-wide attendance statistics."""
    
    total_attendance_records: int = Field(..., description="Total attendance records")
    present_count: int = Field(..., description="Total present records")
    missed_count: int = Field(..., description="Total missed records")
    made_up_count: int = Field(..., description="Total made up records")
    excused_count: int = Field(..., description="Total excused records")
    late_count: int = Field(default=0, description="Total late records")
    partial_count: int = Field(default=0, description="Total partial records")
    
    # NEW: Breakdown by course
    course_breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="Attendance breakdown by course"
    )
    
    # NEW: Trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily attendance trends"
    )
    
    overall_attendance_rate: float = Field(..., description="Overall attendance rate")
    average_attendance_per_student: float = Field(..., description="Average attendance per student")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "AttendanceStatusEnum",
    "MarkedByEnum",
    "AttendanceMark",
    "AttendanceUpdate",
    "WatchRecording",
    "ZoomAttendanceSync",
    "ZoomAttendanceData",
    "AttendanceResponse",
    "MissedSessionResponse",
    "AttendanceSummary",
    "StudentAttendanceSummary",
    "CourseAttendanceResponse",
    "AttendanceListRequest",
    "AttendanceListResponse",
    "AttendanceStatistics",
]