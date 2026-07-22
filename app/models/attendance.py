# ============================================================
# AETHER LINK - ATTENDANCE MODEL ⭐ CRITICAL
# ============================================================
# This is the HEART of your missed sessions feature.
# Powers the student dashboard "Missed Sessions" widget.
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Text, Index, DECIMAL, JSON, BigInteger
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
    LATE = "late"  # NEW: Student attended but arrived late
    PARTIAL = "partial"  # NEW: Student attended part of the session


class MarkedBy(str, enum.Enum):  # NEW
    """Who marked the attendance."""
    SYSTEM = "system"
    TEACHER = "teacher"
    ADMIN = "admin"
    ZOOM_API = "zoom_api"
    VIDEO_AUTO = "video_auto"


class Attendance(Base):
    __tablename__ = "attendances"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # STATUS ⭐ (CRITICAL)
    # ============================================================
    status = Column(
        SQLEnum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]),
        default=AttendanceStatus.MISSED,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # NEW: DURATION & PERCENTAGE TRACKING
    # ============================================================
    duration_attended_minutes = Column(Integer, default=0, nullable=False)
    total_session_minutes = Column(Integer, default=0, nullable=False)
    attendance_percentage = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    
    # ============================================================
    # RECORDING TRACKING ⭐ (CRITICAL)
    # ============================================================
    watched_recording = Column(Boolean, default=False, nullable=False)
    watched_percentage = Column(Integer, default=0, nullable=False)  # 0-100%
    last_watch_time = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Watch duration tracking
    total_watch_time_seconds = Column(Integer, default=0, nullable=False)
    watch_completed_at = Column(DateTime(timezone=True), nullable=True)
    watch_device = Column(String(50), nullable=True)  # mobile, desktop, tablet
    
    # ============================================================
    # NEW: WHO MARKED THE ATTENDANCE
    # ============================================================
    marked_by = Column(
        String(50),
        default=MarkedBy.SYSTEM.value,
        nullable=False
    )
    marked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # NEW: Teacher who marked (if manual)
    marked_by_teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # MAKEUP TRACKING ⭐ (CRITICAL)
    # ============================================================
    made_up_at = Column(DateTime(timezone=True), nullable=True)
    makeup_method = Column(String(50), nullable=True)  # recording, reschedule, assignment, zoom
    makeup_notes = Column(Text, nullable=True)
    
    # NEW: Makeup details
    makeup_reason = Column(String(100), nullable=True)  # WHY they made up (optional)
    makeup_verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    makeup_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: ZOOM API DATA (for auto-attendance)
    # ============================================================
    zoom_attendance_data = Column(JSON, nullable=True)
    # Example: {"join_time": "2024-01-01T10:00:00Z", "leave_time": "2024-01-01T10:45:00Z", "duration": 45}
    
    zoom_sync_at = Column(DateTime(timezone=True), nullable=True)
    zoom_sync_status = Column(String(50), nullable=True)  # pending, synced, failed
    
    # ============================================================
    # NEW: LATE TRACKING
    # ============================================================
    late_minutes = Column(Integer, default=0, nullable=False)  # How many minutes late
    late_reason = Column(Text, nullable=True)
    late_approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    late_approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(Text, nullable=True)
    
    # ============================================================
    # NEW: IP & DEVICE TRACKING
    # ============================================================
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_attendance_unique', 'enrollment_id', 'session_id', unique=True),
        Index('ix_attendance_missed', 'enrollment_id', 'status'),  # CRITICAL for dashboard
        Index('ix_attendance_enrollment_status', 'enrollment_id', 'status'),
        Index('ix_attendance_session_status', 'session_id', 'status'),
        Index('ix_attendance_marked_by', 'marked_by'),
        Index('ix_attendance_watch_percentage', 'watched_percentage'),
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
        foreign_keys=[verified_by],
        uselist=False
    )
    
    # NEW: Marked by teacher
    marked_by_teacher = relationship(
        "User",
        foreign_keys=[marked_by_teacher_id],
        uselist=False
    )
    
    # NEW: Makeup verified by
    makeup_verified_by_user = relationship(
        "User",
        foreign_keys=[makeup_verified_by],
        uselist=False
    )
    
    # NEW: Late approved by
    late_approved_by_user = relationship(
        "User",
        foreign_keys=[late_approved_by],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Attendance {self.id}: {self.status}>"
    
    def __str__(self) -> str:
        return f"{self.enrollment.student.full_name} - Session {self.session.session_number}: {self.status}"
    
    # ============================================================
    # PROPERTIES ⭐ (CRITICAL)
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
    def is_late(self) -> bool:
        """Check if student was late."""
        return self.status == AttendanceStatus.LATE
    
    @property
    def is_partial(self) -> bool:
        """Check if student attended partially."""
        return self.status == AttendanceStatus.PARTIAL
    
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
    
    @property
    def is_auto_marked(self) -> bool:
        """Check if attendance was auto-marked by system."""
        return self.marked_by in [MarkedBy.SYSTEM.value, MarkedBy.ZOOM_API.value, MarkedBy.VIDEO_AUTO.value]
    
    @property
    def is_manually_marked(self) -> bool:
        """Check if attendance was manually marked by teacher/admin."""
        return self.marked_by in [MarkedBy.TEACHER.value, MarkedBy.ADMIN.value]
    
    @property
    def status_display(self) -> str:
        """Get human-readable status."""
        status_map = {
            "present": "Present",
            "missed": "Missed",
            "made_up": "Made Up",
            "excused": "Excused",
            "late": "Late",
            "partial": "Partial",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def marked_by_display(self) -> str:
        """Get human-readable marked by."""
        marked_map = {
            "system": "System",
            "teacher": "Teacher",
            "admin": "Admin",
            "zoom_api": "Zoom API",
            "video_auto": "Auto (Video)",
        }
        return marked_map.get(self.marked_by, "Unknown")
    
    @property
    def watch_progress_display(self) -> str:
        """Get watch progress display."""
        if self.watched_percentage >= 100:
            return "✅ Fully Watched"
        elif self.watched_percentage >= 80:
            return f"🔄 {self.watched_percentage}% - Made Up"
        elif self.watched_percentage > 0:
            return f"⏳ {self.watched_percentage}% Watched"
        return "❌ Not Watched"
    
    # ============================================================
    # METHODS ⭐ (CRITICAL)
    # ============================================================
    
    def mark_present(self, marked_by: str = "teacher", marked_by_id: int = None, verified_by: int = None) -> None:
        """Mark attendance as present."""
        self.status = AttendanceStatus.PRESENT
        self.marked_by = marked_by
        if marked_by_id:
            self.marked_by_teacher_id = marked_by_id
        self.marked_at = func.now()
        if verified_by:
            self.verified_by = verified_by
            self.verified_at = func.now()
    
    def mark_missed(self, marked_by: str = "system") -> None:
        """Mark attendance as missed."""
        self.status = AttendanceStatus.MISSED
        self.marked_by = marked_by
        self.marked_at = func.now()
    
    def mark_made_up(self, method: str = "recording", notes: str = None, reason: str = None) -> None:
        """Mark attendance as made up."""
        self.status = AttendanceStatus.MADE_UP
        self.made_up_at = func.now()
        self.makeup_method = method
        if notes:
            self.makeup_notes = notes
        if reason:
            self.makeup_reason = reason
    
    def mark_excused(self, verified_by: int = None, remarks: str = None) -> None:
        """Mark attendance as excused."""
        self.status = AttendanceStatus.EXCUSED
        self.marked_by = MarkedBy.TEACHER.value
        self.marked_at = func.now()
        if verified_by:
            self.verified_by = verified_by
            self.verified_at = func.now()
        if remarks:
            self.remarks = remarks
    
    def mark_late(self, late_minutes: int, reason: str = None) -> None:
        """Mark attendance as late."""
        self.status = AttendanceStatus.LATE
        self.late_minutes = late_minutes
        if reason:
            self.late_reason = reason
        self.marked_by = MarkedBy.TEACHER.value
        self.marked_at = func.now()
    
    def mark_partial(self, attended_minutes: int, total_minutes: int, marked_by: str = "system") -> None:
        """Mark attendance as partial based on duration."""
        self.status = AttendanceStatus.PARTIAL
        self.duration_attended_minutes = attended_minutes
        self.total_session_minutes = total_minutes
        self.attendance_percentage = (attended_minutes / total_minutes * 100) if total_minutes > 0 else 0
        self.marked_by = marked_by
        self.marked_at = func.now()
    
    def watch_recording(self, percentage: int, device: str = None, watch_duration_seconds: int = None) -> bool:
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
        
        if device:
            self.watch_device = device
        if watch_duration_seconds:
            self.total_watch_time_seconds += watch_duration_seconds
        
        # ⭐ AUTO-MADE-UP: If watched >= 80% and status is MISSED
        if percentage >= 80 and self.is_missed:
            self.mark_made_up(method="recording", reason="auto_80_percent_watch")
            self.watch_completed_at = func.now()
            return True
        
        # If watched 100%, mark as fully watched
        if percentage >= 100:
            self.watch_completed_at = func.now()
        
        return False
    
    def update_zoom_data(self, zoom_data: dict) -> None:
        """Update Zoom attendance data."""
        self.zoom_attendance_data = zoom_data
        self.zoom_sync_at = func.now()
        self.zoom_sync_status = "synced"
        
        # Extract duration if available
        if "duration" in zoom_data:
            self.duration_attended_minutes = zoom_data["duration"]
        
        # Auto-mark based on 60% rule
        if self.total_session_minutes > 0 and self.duration_attended_minutes > 0:
            percentage = (self.duration_attended_minutes / self.total_session_minutes) * 100
            self.attendance_percentage = percentage
            if percentage >= 60:
                self.mark_present(marked_by=MarkedBy.ZOOM_API.value)
            else:
                self.mark_missed(marked_by=MarkedBy.ZOOM_API.value)
    
    def verify(self, verified_by: int) -> None:
        """Verify attendance record."""
        self.verified_by = verified_by
        self.verified_at = func.now()
    
    def approve_late(self, approved_by: int) -> None:
        """Approve a late attendance."""
        self.late_approved_by = approved_by
        self.late_approved_at = func.now()
    
    def set_device_info(self, ip_address: str, user_agent: str, device_type: str = None) -> None:
        """Set device information."""
        self.ip_address = ip_address
        self.user_agent = user_agent
        if device_type:
            self.device_type = device_type
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def verify_makeup(self, verified_by: int) -> None:
        """Verify a makeup attendance."""
        self.makeup_verified_by = verified_by
        self.makeup_verified_at = func.now()
    
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
        allowed_methods = ["recording", "reschedule", "assignment", "zoom"]
        return method in allowed_methods if method else True
    
    @staticmethod
    def validate_late_minutes(minutes: int) -> bool:
        """Validate late minutes."""
        return 0 <= minutes <= 180  # Max 3 hours late
    
    @staticmethod
    def validate_attendance_percentage(percentage: float) -> bool:
        """Validate attendance percentage."""
        return 0 <= percentage <= 100
    
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
        late = sum(1 for r in records if r.is_late)
        partial = sum(1 for r in records if r.is_partial)
        
        attended = present + made_up  # Made up counts as attended
        
        return {
            "total": total,
            "present": present,
            "missed": missed,
            "made_up": made_up,
            "excused": excused,
            "late": late,
            "partial": partial,
            "attended": attended,
            "attendance_percentage": (attended / total * 100) if total > 0 else 0
        }
    
    @classmethod
    def get_missed_sessions_for_student(cls, session, student_id: int, course_id: int = None) -> list:
        """Get all missed sessions for a student (for dashboard)."""
        query = session.query(cls).join(cls.enrollment).filter(
            cls.enrollment.has(student_id=student_id),
            cls.status == AttendanceStatus.MISSED
        )
        
        if course_id:
            query = query.filter(cls.enrollment.has(course_id=course_id))
        
        return query.all()
    
    @classmethod
    def get_attendance_for_session(cls, session, session_id: int) -> list:
        """Get all attendance records for a specific session."""
        return session.query(cls).filter(
            cls.session_id == session_id
        ).all()


# ============================================================
# NEW: ATTENDANCE AUDIT LOG (Audit Trail)
# ============================================================

class AttendanceAuditLog(Base):
    """Track all attendance changes for auditing."""
    __tablename__ = "attendance_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(Integer, ForeignKey("attendances.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # What changed
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    from_percentage = Column(Integer, nullable=True)
    to_percentage = Column(Integer, nullable=True)
    
    # Who changed it
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Why
    reason = Column(Text, nullable=True)
    change_method = Column(String(50), nullable=True)  # manual, auto, zoom, video
    
    # Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    attendance = relationship("Attendance", foreign_keys=[attendance_id])
    changer = relationship("User", foreign_keys=[changed_by])
    
    def __repr__(self) -> str:
        return f"<AttendanceAuditLog {self.id}: {self.from_status} -> {self.to_status}>"