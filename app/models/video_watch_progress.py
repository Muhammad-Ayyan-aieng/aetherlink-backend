# ============================================================
# AETHER LINK - VIDEO WATCH PROGRESS MODEL
# ============================================================
# Purpose: Track student video watching progress for:
# 1. 80% rule → Auto-mark attendance as MADE_UP
# 2. Resume playback across devices
# 3. Analytics on student engagement
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, DECIMAL, Text, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class WatchStatus(str, enum.Enum):
    """Watch progress status."""
    NOT_STARTED = "not_started"
    WATCHING = "watching"
    PAUSED = "paused"
    COMPLETED = "completed"
    MADE_UP = "made_up"  # Reached 80% and auto-marked attendance


class VideoWatchProgress(Base):
    __tablename__ = "video_watch_progress"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # PROGRESS TRACKING ⭐ (CRITICAL)
    # ============================================================
    progress_percentage = Column(Integer, default=0, nullable=False)  # 0-100
    
    # NEW: Detailed progress
    current_position_seconds = Column(Integer, default=0, nullable=False)  # Where they left off
    total_duration_seconds = Column(Integer, default=0, nullable=False)  # Video duration
    last_position_updated_at = Column(DateTime(timezone=True), nullable=True)  # Last position update
    
    # ============================================================
    # WATCH TIME TRACKING
    # ============================================================
    total_watch_time_seconds = Column(BigInteger, default=0, nullable=False)  # Total time watched
    session_watch_time_seconds = Column(Integer, default=0, nullable=False)  # Current session watch time
    watch_started_at = Column(DateTime(timezone=True), nullable=True)  # When they started watching
    last_watch_at = Column(DateTime(timezone=True), nullable=True)  # Last activity
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=WatchStatus.NOT_STARTED.value,
        nullable=False,
        index=True
    )
    
    # NEW: Has been paused by user
    is_paused_by_user = Column(Boolean, default=False, nullable=False)
    
    # NEW: Playback speed
    playback_speed = Column(DECIMAL(3, 2), default=1.00, nullable=False)  # 0.5x, 1.0x, 1.5x, 2.0x
    
    # NEW: Quality
    quality = Column(String(20), nullable=True)  # 360p, 720p, 1080p
    
    # ============================================================
    # ⭐ 80% RULE TRACKING (CRITICAL)
    # ============================================================
    # When progress reaches 80%, attendance is auto-marked as MADE_UP
    made_up_triggered = Column(Boolean, default=False, nullable=False)  # Whether 80% rule was triggered
    made_up_triggered_at = Column(DateTime(timezone=True), nullable=True)  # When 80% was reached
    attendance_id = Column(Integer, ForeignKey("attendances.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # NEW: DEVICE & SESSION INFO
    # ============================================================
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    device_id = Column(String(255), nullable=True)  # Device fingerprint
    browser_name = Column(String(50), nullable=True)
    os_name = Column(String(50), nullable=True)
    ip_address = Column(String(100), nullable=True)
    
    # NEW: Watch session ID (for tracking a single viewing session)
    watch_session_id = Column(String(255), nullable=True, index=True)
    
    # ============================================================
    # NEW: SEGMENT TRACKING (For analytics)
    # ============================================================
    segments_watched = Column(JSON, nullable=True)  # [{"start": 0, "end": 30}, {"start": 45, "end": 60}]
    # Tracks which parts of the video they've watched
    
    # ============================================================
    # NEW: INTERACTIONS
    # ============================================================
    seek_count = Column(Integer, default=0, nullable=False)  # Number of times they seeked
    pause_count = Column(Integer, default=0, nullable=False)  # Number of times they paused
    resume_count = Column(Integer, default=0, nullable=False)  # Number of times they resumed
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    # Example: {"auto_play": true, "fullscreen": false, "captions": "en"}
    
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
        # One progress record per student per material
        Index('ix_video_watch_unique', 'student_id', 'material_id', unique=True),
        # For finding students who need makeup
        Index('ix_video_watch_makeup', 'progress_percentage', 'made_up_triggered'),
        # For active watching sessions
        Index('ix_video_watch_active', 'student_id', 'status'),
        # For attendance linking
        Index('ix_video_watch_attendance', 'attendance_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    student = relationship(
        "User",
        back_populates="video_progress",
        foreign_keys=[student_id]
    )
    
    material = relationship(
        "Material",
        back_populates="watch_progress",
        foreign_keys=[material_id]
    )
    
    attendance = relationship(
        "Attendance",
        foreign_keys=[attendance_id],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<VideoWatchProgress {self.student_id} - {self.material_id}: {self.progress_percentage}%>"
    
    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.material.title}: {self.progress_percentage}%"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_completed(self) -> bool:
        """Check if video is fully watched (100%)."""
        return self.progress_percentage >= 100
    
    @property
    def is_made_up(self) -> bool:
        """Check if 80% rule was triggered."""
        return self.made_up_triggered
    
    @property
    def can_makeup(self) -> bool:
        """Check if progress is at or above 80% but not yet triggered."""
        return self.progress_percentage >= 80 and not self.made_up_triggered
    
    @property
    def is_watching(self) -> bool:
        """Check if currently watching."""
        return self.status == WatchStatus.WATCHING.value
    
    @property
    def is_paused(self) -> bool:
        """Check if paused."""
        return self.status == WatchStatus.PAUSED.value
    
    @property
    def progress_display(self) -> str:
        """Get progress display string."""
        if self.is_completed:
            return "✅ Completed"
        elif self.is_made_up:
            return f"🎯 {self.progress_percentage}% (Made Up)"
        elif self.progress_percentage >= 80:
            return f"🎯 {self.progress_percentage}% (Ready to Make Up)"
        elif self.progress_percentage > 0:
            return f"⏳ {self.progress_percentage}%"
        return "📹 Not Started"
    
    @property
    def remaining_seconds(self) -> int:
        """Get remaining video time in seconds."""
        if self.total_duration_seconds == 0:
            return 0
        remaining = self.total_duration_seconds - self.current_position_seconds
        return max(0, remaining)
    
    @property
    def remaining_percentage(self) -> int:
        """Get remaining percentage to complete."""
        return max(0, 100 - self.progress_percentage)
    
    @property
    def progress_to_makeup(self) -> int:
        """Get percentage needed to reach 80% makeup threshold."""
        if self.progress_percentage >= 80:
            return 0
        return 80 - self.progress_percentage
    
    @property
    def watch_time_display(self) -> str:
        """Get human-readable watch time."""
        return self._format_time(self.total_watch_time_seconds)
    
    @property
    def position_display(self) -> str:
        """Get human-readable current position."""
        return self._format_time(self.current_position_seconds)
    
    @property
    def duration_display(self) -> str:
        """Get human-readable total duration."""
        return self._format_time(self.total_duration_seconds)
    
    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds to HH:MM:SS."""
        if seconds <= 0:
            return "00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    # ============================================================
    # METHODS ⭐ (CRITICAL)
    # ============================================================
    
    def update_progress(
        self, 
        current_position: int, 
        total_duration: int,
        watch_time_added: int = 0,
        device_type: str = None,
        watch_session_id: str = None,
        segment: dict = None
    ) -> bool:
        """
        Update watch progress.
        Returns True if 80% rule was triggered.
        """
        # Update basic progress
        self.current_position_seconds = current_position
        self.total_duration_seconds = total_duration
        
        # Calculate percentage
        if total_duration > 0:
            self.progress_percentage = min(100, int((current_position / total_duration) * 100))
        else:
            self.progress_percentage = 0
        
        # Update watch time
        if watch_time_added > 0:
            self.total_watch_time_seconds += watch_time_added
            self.session_watch_time_seconds += watch_time_added
        
        # Update status
        if self.progress_percentage >= 100:
            self.status = WatchStatus.COMPLETED.value
        else:
            self.status = WatchStatus.WATCHING.value
        
        # Update device info
        if device_type:
            self.device_type = device_type
        if watch_session_id:
            self.watch_session_id = watch_session_id
        
        # Track segment
        if segment:
            if self.segments_watched is None:
                self.segments_watched = []
            self.segments_watched.append(segment)
        
        # ⭐ 80% RULE: Auto-mark attendance as MADE_UP
        triggered = False
        if self.progress_percentage >= 80 and not self.made_up_triggered:
            triggered = self.trigger_makeup()
        
        self.last_watch_at = func.now()
        self.last_position_updated_at = func.now()
        
        return triggered
    
    def trigger_makeup(self, attendance_id: int = None) -> bool:
        """
        Trigger the 80% makeup rule.
        Marks attendance as MADE_UP if there's a corresponding attendance record.
        """
        if self.made_up_triggered:
            return False
        
        self.made_up_triggered = True
        self.made_up_triggered_at = func.now()
        self.status = WatchStatus.MADE_UP.value
        
        # If attendance ID is provided, link it
        if attendance_id:
            self.attendance_id = attendance_id
        
        return True
    
    def mark_paused(self) -> None:
        """Mark video as paused."""
        self.status = WatchStatus.PAUSED.value
        self.is_paused_by_user = True
    
    def mark_resumed(self) -> None:
        """Mark video as resumed."""
        self.status = WatchStatus.WATCHING.value
        self.is_paused_by_user = False
        self.resume_count += 1
    
    def mark_started(self) -> None:
        """Mark video as started."""
        if self.status == WatchStatus.NOT_STARTED.value:
            self.watch_started_at = func.now()
        self.status = WatchStatus.WATCHING.value
        self.watch_session_id = func.uuid4()
    
    def increment_seek(self) -> None:
        """Increment seek count."""
        self.seek_count += 1
    
    def increment_pause(self) -> None:
        """Increment pause count."""
        self.pause_count += 1
    
    def reset_session(self) -> None:
        """Reset session watch time."""
        self.session_watch_time_seconds = 0
    
    def set_playback_speed(self, speed: float) -> None:
        """Set playback speed."""
        if 0.5 <= speed <= 2.0:
            self.playback_speed = speed
    
    def set_quality(self, quality: str) -> None:
        """Set video quality."""
        self.quality = quality
    
    def set_device_info(self, device_type: str, device_id: str = None, browser: str = None, os: str = None, ip: str = None) -> None:
        """Set device information."""
        if device_type:
            self.device_type = device_type
        if device_id:
            self.device_id = device_id
        if browser:
            self.browser_name = browser
        if os:
            self.os_name = os
        if ip:
            self.ip_address = ip
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete(self) -> None:
        """Soft delete the progress record."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_progress(progress: int) -> bool:
        """Validate progress is within limits."""
        return 0 <= progress <= 100
    
    @staticmethod
    def validate_position(position: int, duration: int) -> bool:
        """Validate position is within video duration."""
        return 0 <= position <= duration
    
    @staticmethod
    def validate_playback_speed(speed: float) -> bool:
        """Validate playback speed."""
        return 0.5 <= speed <= 2.0
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert watch progress to dictionary."""
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "material_id": self.material_id,
            "material_title": self.material.title if self.material else None,
            "progress_percentage": self.progress_percentage,
            "progress_display": self.progress_display,
            "status": self.status,
            "is_completed": self.is_completed,
            "is_made_up": self.is_made_up,
            "can_makeup": self.can_makeup,
            "current_position_seconds": self.current_position_seconds,
            "position_display": self.position_display,
            "total_duration_seconds": self.total_duration_seconds,
            "duration_display": self.duration_display,
            "remaining_seconds": self.remaining_seconds,
            "remaining_percentage": self.remaining_percentage,
            "progress_to_makeup": self.progress_to_makeup,
            "total_watch_time_seconds": self.total_watch_time_seconds,
            "watch_time_display": self.watch_time_display,
            "playback_speed": float(self.playback_speed) if self.playback_speed else 1.0,
            "quality": self.quality,
            "device_type": self.device_type,
            "last_watch_at": self.last_watch_at.isoformat() if self.last_watch_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "made_up_triggered": self.made_up_triggered,
                "made_up_triggered_at": self.made_up_triggered_at.isoformat() if self.made_up_triggered_at else None,
                "attendance_id": self.attendance_id,
                "watch_started_at": self.watch_started_at.isoformat() if self.watch_started_at else None,
                "session_watch_time_seconds": self.session_watch_time_seconds,
                "is_paused_by_user": self.is_paused_by_user,
                "seek_count": self.seek_count,
                "pause_count": self.pause_count,
                "resume_count": self.resume_count,
                "segments_watched": self.segments_watched,
                "device_id": self.device_id,
                "browser_name": self.browser_name,
                "os_name": self.os_name,
                "ip_address": self.ip_address,
                "watch_session_id": self.watch_session_id,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing progress data."""
        data = self.to_dict()
        # Remove sensitive fields
        data.pop("ip_address", None)
        data.pop("device_id", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing progress data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: VIDEO WATCH ANALYTICS
# ============================================================

class VideoWatchAnalytics(Base):
    """Aggregated video watch analytics."""
    __tablename__ = "video_watch_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Daily stats
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Watch stats
    total_watches = Column(Integer, default=0, nullable=False)
    unique_viewers = Column(Integer, default=0, nullable=False)
    total_watch_time_seconds = Column(BigInteger, default=0, nullable=False)
    avg_watch_time_seconds = Column(Integer, default=0, nullable=False)
    avg_watch_percentage = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    
    # Completion stats
    completed_count = Column(Integer, default=0, nullable=False)
    completion_rate = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    
    # 80% rule stats
    made_up_triggered_count = Column(Integer, default=0, nullable=False)
    
    # Device stats
    mobile_views = Column(Integer, default=0, nullable=False)
    desktop_views = Column(Integer, default=0, nullable=False)
    tablet_views = Column(Integer, default=0, nullable=False)
    
    # Timestamp
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    material = relationship("Material", foreign_keys=[material_id])
    
    __table_args__ = (
        Index('ix_video_analytics_material_date', 'material_id', 'date', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<VideoWatchAnalytics {self.material_id} - {self.date}>"