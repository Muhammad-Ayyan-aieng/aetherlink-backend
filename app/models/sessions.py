# ============================================================
# AETHER LINK - SESSION MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, JSON, Boolean, Index
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


class Session(Base):
    __tablename__ = "sessions"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # COURSE RELATIONSHIP
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # ============================================================
    # SESSION METADATA
    # ============================================================
    session_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # ============================================================
    # SCHEDULE
    # ============================================================
    date_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60, nullable=False)
    
    # ============================================================
    # ZOOM INTEGRATION
    # ============================================================
    zoom_meeting_id = Column(String(100), nullable=False)
    zoom_join_url = Column(String(500), nullable=True)
    zoom_start_url = Column(String(500), nullable=True)
    zoom_password = Column(String(20), nullable=True)
    
    # ============================================================
    # RECORDING (REQUIRED)
    # ============================================================
    recording_url = Column(String(500), nullable=False)  # ✅ REQUIRED
    recording_available = Column(Boolean, default=False, nullable=False)
    recording_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        SQLEnum(SessionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SessionStatus.UPCOMING,
        nullable=False
    )
    
    # ============================================================
    # ADDITIONAL METADATA
    # ============================================================
    meeting_notes = Column(Text, nullable=True)
    resources = Column(JSON, nullable=True)  # For additional resources
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        # Ensure unique session numbers per course
        Index('ix_sessions_course_number', 'course_id', 'session_number', unique=True),
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
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Session {self.session_number}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # HELPER METHODS
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
    
    def mark_live(self) -> None:
        """Mark session as live."""
        self.status = SessionStatus.LIVE
    
    def mark_completed(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
    
    def mark_cancelled(self) -> None:
        """Mark session as cancelled."""
        self.status = SessionStatus.CANCELLED
    
    def add_recording(self, url: str) -> None:
        """Add recording URL and mark as available."""
        self.recording_url = url
        self.recording_available = True
        self.recording_processed_at = func.now()
    
    def remove_recording(self) -> None:
        """Remove recording."""
        self.recording_url = None
        self.recording_available = False
        self.recording_processed_at = None
    
    def soft_delete(self) -> None:
        """Soft delete the session."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted session."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION (Future - used in schemas)
    # ============================================================
    
    @staticmethod
    def validate_duration(duration: int) -> bool:
        """Validate duration is within limits."""
        return 1 <= duration <= 180  # Max 3 hours
