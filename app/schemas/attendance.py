# ============================================================
# AETHER LINK - ATTENDANCE SCHEMAS ⭐ CRITICAL
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# ATTENDANCE STATUS ENUM
# ============================================================

class AttendanceStatusEnum(str, Enum):
    """Attendance status enumeration for schemas."""
    PRESENT = "present"
    MISSED = "missed"
    MADE_UP = "made_up"
    EXCUSED = "excused"


# ============================================================
# ATTENDANCE MARK SCHEMA (Teacher/Admin)
# ============================================================

class AttendanceMark(BaseModel):
    """Schema for marking student attendance."""
    
    enrollment_id: int = Field(..., gt=0, description="Enrollment ID")
    session_id: int = Field(..., gt=0, description="Session ID")
    status: AttendanceStatusEnum = Field(..., description="Attendance status")
    remarks: Optional[str] = Field(None, max_length=500, description="Teacher remarks")
    
    @validator('status')
    def validate_status(cls, v: AttendanceStatusEnum) -> AttendanceStatusEnum:
        """Validate status."""
        if v == AttendanceStatusEnum.MADE_UP:
            raise ValueError('Cannot mark as made_up directly. Use watch recording endpoint.')
        return v


# ============================================================
# ATTENDANCE UPDATE SCHEMA
# ============================================================

class AttendanceUpdate(BaseModel):
    """Schema for updating attendance record."""
    
    status: Optional[AttendanceStatusEnum] = Field(None, description="Attendance status")
    remarks: Optional[str] = Field(None, max_length=500, description="Remarks")
    verified: Optional[bool] = Field(None, description="Verify attendance")


# ============================================================
# WATCH RECORDING SCHEMA ⭐ CRITICAL
# ============================================================

class WatchRecording(BaseModel):
    """Schema for student watching a recording."""
    
    watched_percentage: int = Field(..., ge=0, le=100, description="Percentage of recording watched (0-100)")
    
    @validator('watched_percentage')
    def validate_percentage(cls, v: int) -> int:
        """Ensure percentage is between 0 and 100."""
        if v < 0:
            return 0
        if v > 100:
            return 100
        return v


# ============================================================
# BULK ATTENDANCE MARK SCHEMA
# ============================================================

class BulkAttendanceMark(BaseModel):
    """Schema for marking multiple students attendance."""
    
    session_id: int = Field(..., gt=0, description="Session ID")
    present_student_ids: List[int] = Field(default=[], description="List of present student IDs")
    excused_student_ids: List[int] = Field(default=[], description="List of excused student IDs")
    
    @validator('present_student_ids', 'excused_student_ids')
    def validate_unique_students(cls, v: List[int]) -> List[int]:
        """Ensure no duplicate student IDs."""
        if len(v) != len(set(v)):
            raise ValueError('Duplicate student IDs found')
        return v


# ============================================================
# ATTENDANCE RESPONSE SCHEMA
# ============================================================

class AttendanceResponse(BaseModel):
    """Schema for attendance record response."""
    
    id: int = Field(..., description="Attendance ID")
    enrollment_id: int = Field(..., description="Enrollment ID")
    session_id: int = Field(..., description="Session ID")
    status: AttendanceStatusEnum = Field(..., description="Attendance status")
    
    watched_recording: bool = Field(False, description="Watched recording?")
    watched_percentage: int = Field(0, description="Watched percentage (0-100)")
    last_watch_time: Optional[datetime] = Field(None, description="Last watch time")
    
    made_up_at: Optional[datetime] = Field(None, description="Made up timestamp")
    makeup_method: Optional[str] = Field(None, description="Makeup method")
    makeup_notes: Optional[str] = Field(None, description="Makeup notes")
    
    verified_by: Optional[int] = Field(None, description="Verified by (admin ID)")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    remarks: Optional[str] = Field(None, description="Remarks")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


# ============================================================
# MISSED SESSION RESPONSE ⭐ CRITICAL
# ============================================================

class MissedSessionResponse(BaseModel):
    """Schema for missed session on student dashboard."""
    
    session_id: int = Field(..., description="Session ID")
    session_number: int = Field(..., description="Session number")
    session_title: str = Field(..., description="Session title")
    session_date: datetime = Field(..., description="Session date")
    
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    course_slug: str = Field(..., description="Course slug")
    
    recording_url: Optional[str] = Field(None, description="Recording URL")
    recording_available: bool = Field(False, description="Recording available?")
    can_makeup: bool = Field(False, description="Can make up?")
    
    watched_percentage: int = Field(0, description="Watched percentage")
    days_ago: int = Field(..., description="Days since session")
    status: AttendanceStatusEnum = Field(..., description="Current status")


# ============================================================
# ATTENDANCE SUMMARY SCHEMA
# ============================================================

class AttendanceSummary(BaseModel):
    student_id: int
    course_id: Optional[int] = None
    total_sessions: int = 0
    present: int = 0
    absent: int = 0          # ← Add this
    missed: int = 0
    made_up: int = 0
    excused: int = 0         # ← Add this
    attendance_rate: float = 0.0  # ← Change from attendance_percentage
    attendance_percentage: float = 0.0  # ← Keep for compatibility
    missed_count: int = 0
    missed_can_be_made_up: bool = False


# ============================================================
# COURSE ATTENDANCE SUMMARY (Teacher View)
# ============================================================

class StudentAttendanceSummary(BaseModel):
    """Schema for per-student attendance summary (teacher view)."""
    
    student_id: int = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    student_email: str = Field(..., description="Student email")
    
    total_sessions: int = Field(..., description="Total sessions")
    present: int = Field(..., description="Present sessions")
    missed: int = Field(..., description="Missed sessions")
    made_up: int = Field(..., description="Made up sessions")
    excused: int = Field(..., description="Excused sessions")
    attendance_percentage: float = Field(..., description="Attendance percentage")


class CourseAttendanceResponse(BaseModel):
    """Schema for course attendance report."""
    
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    students: List[StudentAttendanceSummary] = Field(..., description="Student attendance data")


# ============================================================
# ATTENDANCE LIST RESPONSE
# ============================================================

class AttendanceListResponse(BaseModel):
    """Schema for paginated attendance list response."""
    
    attendances: List[AttendanceResponse] = Field(..., description="List of attendance records")
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "AttendanceStatusEnum",
    "AttendanceMark",
    "AttendanceUpdate",
    "WatchRecording",
    "BulkAttendanceMark",
    "AttendanceResponse",
    "MissedSessionResponse",
    "AttendanceSummary",
    "StudentAttendanceSummary",
    "CourseAttendanceResponse",
    "AttendanceListResponse",
]