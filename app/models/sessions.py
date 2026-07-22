# ============================================================
# AETHER LINK - SESSION MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, JSON, Boolean, Index, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionType(str, enum.Enum):  # NEW
    """Session type enumeration."""
    LECTURE = "lecture"
    LAB = "lab"
    QUIZ = "quiz"
    REVIEW = "review"
    WORKSHOP = "workshop"
    OFFICE_HOURS = "office_hours"
    OTHER = "other"


class Session(Base):
    __tablename__ = "sessions"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # COURSE RELATIONSHIP
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # SESSION METADATA
    # ============================================================
    session_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # NEW: Session type
    session_type = Column(
        String(50),
        default=SessionType.LECTURE.value,
        nullable=False
    )
    
    # ============================================================
    # SCHEDULE
    # ============================================================
    date_time = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60, nullable=False)
    
    # NEW: End time (calculated from start + duration)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Timezone
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # ============================================================
    # ZOOM INTEGRATION
    # ============================================================
    zoom_meeting_id = Column(String(100), nullable=True, index=True)
    zoom_join_url = Column(String(500), nullable=True)
    zoom_start_url = Column(String(500), nullable=True)
    zoom_password = Column(String(20), nullable=True)
    
    # NEW: Zoom meeting settings
    zoom_settings = Column(JSON, nullable=True)
    # Example: {"auto_record": true, "waiting_room": false, "mute_on_entry": true}
    
    # NEW: Zoom meeting status
    zoom_meeting_status = Column(String(50), nullable=True)  # waiting, started, ended
    
    # ============================================================
    # RECORDING
    # ============================================================
    recording_url = Column(String(500), nullable=True)  # Made optional (allow NULL)
    recording_available = Column(Boolean, default=False, nullable=False)
    recording_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Recording metadata
    recording_duration_minutes = Column(Integer, nullable=True)
    recording_file_size = Column(BigInteger, nullable=True)  # In bytes
    recording_mime_type = Column(String(50), nullable=True)
    
    # NEW: Recording download URL (separate from streaming URL)
    recording_download_url = Column(String(500), nullable=True)
    
    # NEW: Recording transcript (if available)
    recording_transcript = Column(Text, nullable=True)
    recording_transcript_url = Column(String(500), nullable=True)
    
    # ============================================================
    # NEW: IS LIVE / RECORDED FLAGS
    # ============================================================
    is_live = Column(Boolean, default=True, nullable=False)
    is_recorded = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        SQLEnum(SessionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SessionStatus.UPCOMING,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # NEW: ATTENDANCE STATISTICS (Cached)
    # ============================================================
    total_students = Column(Integer, default=0, nullable=False)
    present_count = Column(Integer, default=0, nullable=False)
    absent_count = Column(Integer, default=0, nullable=False)
    made_up_count = Column(Integer, default=0, nullable=False)
    attendance_percentage = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # NEW: STREAMING INFO
    # ============================================================
    stream_url = Column(String(500), nullable=True)  # For embedded video
    stream_key = Column(String(100), nullable=True)  # For stream authentication
    stream_platform = Column(String(50), nullable=True)  # zoom, youtube, vimeo, custom
    
    # ============================================================
    # NEW: MATERIALS (Foreign key to materials table)
    # ============================================================
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # ADDITIONAL METADATA
    # ============================================================
    meeting_notes = Column(Text, nullable=True)
    resources = Column(JSON, nullable=True)  # For additional resources
    
    # NEW: Instructor notes (private)
    instructor_notes = Column(Text, nullable=True)
    
    # NEW: Student instructions
    student_instructions = Column(Text, nullable=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_sessions_course_number', 'course_id', 'session_number', unique=True),
        Index('ix_sessions_date_time_status', 'date_time', 'status'),
        Index('ix_sessions_course_status', 'course_id', 'status'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship(
        "Course",
        back_populates="sessions",
        foreign_keys=[course_id]
    )
    
    attendance_records = relationship(
        "Attendance",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    # NEW: Materials relationship (many-to-one)
    material = relationship(
        "Material",
        foreign_keys=[material_id],
        uselist=False
    )
    
    # NEW: Session materials (many-to-many)
    session_materials = relationship(
        "SessionMaterial",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Session {self.session_number}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_upcoming(self) -> bool:
        """Check if session is upcoming."""
        return self.status == SessionStatus.UPCOMING
    
    @property
    def is_live(self) -> bool:
        """Check if session is live."""
        return self.status == SessionStatus.LIVE
    
    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.status == SessionStatus.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if session is cancelled."""
        return self.status == SessionStatus.CANCELLED
    
    @property
    def has_recording(self) -> bool:
        """Check if recording is available."""
        return self.recording_available and self.recording_url is not None
    
    @property
    def is_lecture(self) -> bool:
        """Check if session is a lecture."""
        return self.session_type == SessionType.LECTURE.value
    
    @property
    def is_lab(self) -> bool:
        """Check if session is a lab."""
        return self.session_type == SessionType.LAB.value
    
    @property
    def is_quiz(self) -> bool:
        """Check if session is a quiz."""
        return self.session_type == SessionType.QUIZ.value
    
    @property
    def is_workshop(self) -> bool:
        """Check if session is a workshop."""
        return self.session_type == SessionType.WORKSHOP.value
    
    @property
    def is_office_hours(self) -> bool:
        """Check if session is office hours."""
        return self.session_type == SessionType.OFFICE_HOURS.value
    
    @property
    def has_zoom_meeting(self) -> bool:
        """Check if session has a Zoom meeting."""
        return self.zoom_meeting_id is not None
    
    @property
    def has_stream(self) -> bool:
        """Check if session has a stream URL."""
        return self.stream_url is not None
    
    @property
    def is_past(self) -> bool:
        """Check if session is in the past."""
        if self.date_time is None:
            return False
        return self.date_time < func.now()
    
    @property
    def is_future(self) -> bool:
        """Check if session is in the future."""
        if self.date_time is None:
            return False
        return self.date_time > func.now()
    
    @property
    def is_ongoing(self) -> bool:
        """Check if session is currently ongoing."""
        if self.date_time is None or self.duration_minutes is None:
            return False
        session_end = self.date_time + func.interval(f'{self.duration_minutes} minutes')
        return self.date_time <= func.now() <= session_end
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_ongoing and self.status == SessionStatus.UPCOMING:
            return "Ongoing"
        status_map = {
            "upcoming": "Upcoming",
            "live": "Live",
            "completed": "Completed",
            "cancelled": "Cancelled",
        }
        return status_map.get(self.status.value if self.status else None, "Unknown")
    
    @property
    def display_type(self) -> str:
        """Get human-readable session type."""
        type_map = {
            "lecture": "Lecture",
            "lab": "Lab",
            "quiz": "Quiz",
            "review": "Review Session",
            "workshop": "Workshop",
            "office_hours": "Office Hours",
            "other": "Other",
        }
        return type_map.get(self.session_type, "Lecture")
    
    @property
    def formatted_duration(self) -> str:
        """Get formatted duration string."""
        if self.duration_minutes is None:
            return "N/A"
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"
    
    @property
    def attendance_summary(self) -> dict:
        """Get attendance summary."""
        return {
            "total": self.total_students,
            "present": self.present_count,
            "absent": self.absent_count,
            "made_up": self.made_up_count,
            "percentage": self.attendance_percentage,
        }
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def mark_live(self) -> None:
        """Mark session as live."""
        self.status = SessionStatus.LIVE
    
    def mark_completed(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
    
    def mark_cancelled(self) -> None:
        """Mark session as cancelled."""
        self.status = SessionStatus.CANCELLED
    
    def add_recording(self, url: str, duration_minutes: int = None, file_size: int = None, mime_type: str = None) -> None:
        """
        Add recording URL and mark as available.
        
        Args:
            url: Recording URL
            duration_minutes: Duration of recording
            file_size: File size in bytes
            mime_type: MIME type of the recording
        """
        self.recording_url = url
        self.recording_available = True
        self.recording_processed_at = func.now()
        
        if duration_minutes:
            self.recording_duration_minutes = duration_minutes
        if file_size:
            self.recording_file_size = file_size
        if mime_type:
            self.recording_mime_type = mime_type
    
    def add_recording_download(self, download_url: str) -> None:
        """Add recording download URL."""
        self.recording_download_url = download_url
    
    def add_recording_transcript(self, transcript: str, transcript_url: str = None) -> None:
        """Add recording transcript."""
        self.recording_transcript = transcript
        if transcript_url:
            self.recording_transcript_url = transcript_url
    
    def remove_recording(self) -> None:
        """Remove recording."""
        self.recording_url = None
        self.recording_download_url = None
        self.recording_available = False
        self.recording_processed_at = None
        self.recording_duration_minutes = None
        self.recording_file_size = None
        self.recording_mime_type = None
    
    def set_zoom_meeting(self, meeting_id: str, join_url: str, start_url: str = None, password: str = None) -> None:
        """Set Zoom meeting details."""
        self.zoom_meeting_id = meeting_id
        self.zoom_join_url = join_url
        if start_url:
            self.zoom_start_url = start_url
        if password:
            self.zoom_password = password
    
    def set_stream(self, url: str, platform: str, stream_key: str = None) -> None:
        """Set stream details."""
        self.stream_url = url
        self.stream_platform = platform
        if stream_key:
            self.stream_key = stream_key
    
    def update_attendance_stats(self) -> None:
        """Update attendance statistics."""
        total = self.total_students
        if total == 0:
            self.attendance_percentage = 0
            return
        
        present = self.present_count or 0
        made_up = self.made_up_count or 0
        attended = present + made_up
        self.attendance_percentage = int((attended / total) * 100)
    
    def increment_present_count(self) -> None:
        """Increment present count."""
        self.present_count += 1
        self.update_attendance_stats()
    
    def increment_absent_count(self) -> None:
        """Increment absent count."""
        self.absent_count += 1
        self.update_attendance_stats()
    
    def increment_made_up_count(self) -> None:
        """Increment made up count."""
        self.made_up_count += 1
        self.update_attendance_stats()
    
    def set_student_count(self, count: int) -> None:
        """Set total students count."""
        self.total_students = count
        self.update_attendance_stats()
    
    def soft_delete(self) -> None:
        """Soft delete the session."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted session."""
        self.deleted_at = None
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_duration(duration: int) -> bool:
        """Validate duration is within limits."""
        return 1 <= duration <= 480  # Max 8 hours
    
    @staticmethod
    def validate_session_number(number: int) -> bool:
        """Validate session number."""
        return number > 0
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate title length."""
        return 3 <= len(title) <= 255
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert session to dictionary."""
        data = {
            "id": self.id,
            "course_id": self.course_id,
            "session_number": self.session_number,
            "title": self.title,
            "description": self.description,
            "session_type": self.session_type,
            "display_type": self.display_type,
            "date_time": self.date_time.isoformat() if self.date_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "formatted_duration": self.formatted_duration,
            "status": self.status.value if self.status else None,
            "display_status": self.display_status,
            "is_live": self.is_live,
            "is_recorded": self.is_recorded,
            "is_upcoming": self.is_upcoming,
            "is_completed": self.is_completed,
            "is_ongoing": self.is_ongoing,
            "has_recording": self.has_recording,
            "has_zoom_meeting": self.has_zoom_meeting,
            "has_stream": self.has_stream,
            "recording_available": self.recording_available,
            "zoom_join_url": self.zoom_join_url,
            "attendance_summary": self.attendance_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "recording_url": self.recording_url,
                "recording_download_url": self.recording_download_url,
                "recording_duration_minutes": self.recording_duration_minutes,
                "recording_file_size": self.recording_file_size,
                "recording_transcript": self.recording_transcript,
                "recording_transcript_url": self.recording_transcript_url,
                "zoom_meeting_id": self.zoom_meeting_id,
                "zoom_start_url": self.zoom_start_url,
                "zoom_password": self.zoom_password,
                "zoom_settings": self.zoom_settings,
                "stream_key": self.stream_key,
                "meeting_notes": self.meeting_notes,
                "instructor_notes": self.instructor_notes,
                "student_instructions": self.student_instructions,
                "resources": self.resources,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing session data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("zoom_meeting_id", None)
        data.pop("zoom_start_url", None)
        data.pop("zoom_password", None)
        data.pop("zoom_settings", None)
        data.pop("stream_key", None)
        data.pop("meeting_notes", None)
        data.pop("instructor_notes", None)
        data.pop("student_instructions", None)
        data.pop("metadata", None)
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing session data."""
        data = self.to_public_json()
        data.update({
            "can_access": self.is_active or self.is_completed,
            "recording_url": self.recording_url if self.recording_available else None,
            "has_missed": False,  # Will be set by service
        })
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing session data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: SESSION MATERIAL (Many-to-Many)
# ============================================================

class SessionMaterial(Base):
    """Many-to-many relationship between sessions and materials."""
    __tablename__ = "session_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)  # Order within session
    
    # Relationships
    session = relationship("Session", back_populates="session_materials")
    material = relationship("Material", back_populates="session_materials")
    
    __table_args__ = (
        Index('ix_session_materials_unique', 'session_id', 'material_id', unique=True),
    )