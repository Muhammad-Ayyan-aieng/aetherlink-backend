# ============================================================
# AETHER LINK - ATTENDANCE MODEL ⭐ CRITICAL
# ============================================================
# This is the HEART of your missed sessions feature.
# Powers the student dashboard "Missed Sessions" widget.
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class AttendanceStatus(str, enum.Enum):
    """Attendance status enumeration."""
    PRESENT = "present"
    MISSED = "missed"
    MADE_UP = "made_up"
    EXCUSED = "excused"


class Attendance(Base):
    __tablename__ = "attendances"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # ============================================================
    # STATUS ⭐ (CRITICAL)
    # ============================================================
    status = Column(
        SQLEnum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]),
        default=AttendanceStatus.MISSED,
        nullable=False
    )
    
    # ============================================================
    # RECORDING TRACKING ⭐ (CRITICAL)
    # ============================================================
    watched_recording = Column(Boolean, default=False, nullable=False)
    watched_percentage = Column(Integer, default=0, nullable=False)  # 0-100%
    last_watch_time = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # MAKEUP TRACKING ⭐ (CRITICAL)
    # ============================================================
    made_up_at = Column(DateTime(timezone=True), nullable=True)
    makeup_method = Column(String(50), nullable=True)  # recording, reschedule, assignment
    makeup_notes = Column(Text, nullable=True)
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(Text, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        # Prevent duplicate attendance records per student per session
        Index('ix_attendance_unique', 'enrollment_id', 'session_id', unique=True),
        # Track missed sessions for dashboard widget
        Index('ix_attendance_missed', 'enrollment_id', 'status'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment = relationship(
        "Enrollment",
        back_populates="attendance_records",
        foreign_keys=[enrollment_id]
    )
    
    session = relationship(
        "Session",
        back_populates="attendance_records",
        foreign_keys=[session_id]
    )
    
    verified_by_user = relationship(
        "User",
        foreign_keys=[verified_by]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Attendance {self.id}: {self.status}>"
    
    def __str__(self) -> str:
        return f"{self.enrollment.student.full_name} - Session {self.session.session_number}: {self.status}"
    
    # ============================================================
    # HELPER METHODS ⭐ (CRITICAL)
    # ============================================================
    
    @property
    def is_present(self) -> bool:
        """Check if student was present."""
        return self.status == AttendanceStatus.PRESENT
    
    @property
    def is_missed(self) -> bool:
        """Check if student missed the session."""
        return self.status == AttendanceStatus.MISSED
    
    @property
    def is_made_up(self) -> bool:
        """Check if student made up the missed session."""
        return self.status == AttendanceStatus.MADE_UP
    
    @property
    def is_excused(self) -> bool:
        """Check if student was excused."""
        return self.status == AttendanceStatus.EXCUSED
    
    @property
    def can_makeup(self) -> bool:
        """Check if student can make up this missed session."""
        return (
            self.is_missed and
            self.session.recording_available and
            self.session.recording_url is not None
        )
    
    @property
    def is_fully_watched(self) -> bool:
        """Check if student watched 100% of recording."""
        return self.watched_percentage >= 100
    
    @property
    def has_made_up(self) -> bool:
        """Check if student has already made up."""
        return self.is_made_up or self.made_up_at is not None
    
    def mark_present(self, verified_by: int = None) -> None:
        """Mark attendance as present."""
        self.status = AttendanceStatus.PRESENT
        if verified_by:
            self.verified_by = verified_by
            self.verified_at = func.now()
    
    def mark_missed(self) -> None:
        """Mark attendance as missed."""
        self.status = AttendanceStatus.MISSED
    
    def mark_made_up(self, method: str = "recording", notes: str = None) -> None:
        """Mark attendance as made up."""
        self.status = AttendanceStatus.MADE_UP
        self.made_up_at = func.now()
        self.makeup_method = method
        if notes:
            self.makeup_notes = notes
    
    def mark_excused(self, verified_by: int = None, remarks: str = None) -> None:
        """Mark attendance as excused."""
        self.status = AttendanceStatus.EXCUSED
        if verified_by:
            self.verified_by = verified_by
            self.verified_at = func.now()
        if remarks:
            self.remarks = remarks
    
    def watch_recording(self, percentage: int) -> bool:
        """
        Update recording watch progress.
        Returns True if status changed to MADE_UP.
        """
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
        
        self.watched_recording = True
        self.watched_percentage = percentage
        self.last_watch_time = func.now()
        
        # ⭐ AUTO-MADE-UP: If watched >= 80% and status is MISSED
        if percentage >= 80 and self.is_missed:
            self.mark_made_up(method="recording")
            return True
        
        return False
    
    def verify(self, verified_by: int) -> None:
        """Verify attendance record."""
        self.verified_by = verified_by
        self.verified_at = func.now()
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def validate_watch_percentage(percentage: int) -> bool:
        """Validate watch percentage is within limits."""
        return 0 <= percentage <= 100
    
    @staticmethod
    def validate_makeup_method(method: str) -> bool:
        """Validate makeup method."""
        allowed_methods = ["recording", "reschedule", "assignment"]
        return method in allowed_methods if method else True
    
    # ============================================================
    # CLASS METHODS (For bulk operations)
    # ============================================================
    
    @classmethod
    def get_missed_count(cls, session, enrollment_id: int) -> int:
        """Get count of missed sessions for a student."""
        return session.query(cls).filter(
            cls.enrollment_id == enrollment_id,
            cls.status == AttendanceStatus.MISSED
        ).count()
    
    @classmethod
    def get_attendance_summary(cls, session, enrollment_id: int) -> dict:
        """Get attendance summary for a student."""
        records = session.query(cls).filter(
            cls.enrollment_id == enrollment_id
        ).all()
        
        total = len(records)
        present = sum(1 for r in records if r.is_present)
        missed = sum(1 for r in records if r.is_missed)
        made_up = sum(1 for r in records if r.is_made_up)
        excused = sum(1 for r in records if r.is_excused)
        
        return {
            "total": total,
            "present": present,
            "missed": missed,
            "made_up": made_up,
            "excused": excused,
            "attendance_percentage": (present / total * 100) if total > 0 else 0
        }
