# ============================================================
# AETHER LINK - SESSION REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.sessions import Session, SessionStatus
from ..models.course import Course
from ..models.enrollment import Enrollment
from ..models.attendance import Attendance, AttendanceStatus


class SessionRepository(BaseRepository[Session]):
    """Repository for Session model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Session)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_course(self, course_id: int) -> List[Session]:
        """Get all sessions for a course."""
        return self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.deleted_at.is_(None)
        ).order_by(Session.session_number).all()
    
    def get_by_course_paginated(
        self, 
        course_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Session], int]:
        """Get paginated sessions for a course."""
        query = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.deleted_at.is_(None)
        ).order_by(Session.session_number)
        
        total = query.count()
        sessions = query.offset(skip).limit(limit).all()
        return sessions, total
    
    def get_by_status(self, status: SessionStatus) -> List[Session]:
        """Get sessions by status."""
        return self.db.query(Session).filter(
            Session.status == status,
            Session.deleted_at.is_(None)
        ).all()
    
    def get_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        course_id: Optional[int] = None
    ) -> List[Session]:
        """Get sessions within a date range."""
        query = self.db.query(Session).filter(
            Session.date_time >= start_date,
            Session.date_time <= end_date,
            Session.deleted_at.is_(None)
        )
        
        if course_id:
            query = query.filter(Session.course_id == course_id)
        
        return query.order_by(Session.date_time).all()
    
    # ============================================================
    # STATUS-BASED QUERIES
    # ============================================================
    
    def get_upcoming(self, course_id: Optional[int] = None) -> List[Session]:
        """Get upcoming sessions."""
        query = self.db.query(Session).filter(
            Session.date_time > datetime.utcnow(),
            Session.status == SessionStatus.UPCOMING,
            Session.deleted_at.is_(None)
        ).order_by(Session.date_time)
        
        if course_id:
            query = query.filter(Session.course_id == course_id)
        
        return query.all()
    
    def get_live(self) -> List[Session]:
        """Get currently live sessions."""
        now = datetime.utcnow()
        return self.db.query(Session).filter(
            Session.status == SessionStatus.LIVE,
            Session.deleted_at.is_(None)
        ).all()
    
    def get_completed(self, course_id: Optional[int] = None) -> List[Session]:
        """Get completed sessions."""
        query = self.db.query(Session).filter(
            Session.status == SessionStatus.COMPLETED,
            Session.deleted_at.is_(None)
        ).order_by(Session.date_time.desc())
        
        if course_id:
            query = query.filter(Session.course_id == course_id)
        
        return query.all()
    
    def get_cancelled(self) -> List[Session]:
        """Get cancelled sessions."""
        return self.db.query(Session).filter(
            Session.status == SessionStatus.CANCELLED,
            Session.deleted_at.is_(None)
        ).all()
    
    def get_today_sessions(self) -> List[Session]:
        """Get today's sessions."""
        today = datetime.utcnow().date()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        
        return self.db.query(Session).filter(
            Session.date_time >= start,
            Session.date_time <= end,
            Session.deleted_at.is_(None)
        ).order_by(Session.date_time).all()
    
    # ============================================================
    # RELATIONSHIP QUERIES
    # ============================================================
    
    def get_with_attendance(self, session_id: int) -> Optional[Session]:
        """Get session with attendance records loaded."""
        return self.db.query(Session).options(
            joinedload(Session.attendance_records)
        ).filter(
            Session.id == session_id,
            Session.deleted_at.is_(None)
        ).first()
    
    def get_with_course(self, session_id: int) -> Optional[Session]:
        """Get session with course loaded."""
        return self.db.query(Session).options(
            joinedload(Session.course)
        ).filter(
            Session.id == session_id,
            Session.deleted_at.is_(None)
        ).first()
    
    def get_full_details(self, session_id: int) -> Optional[Session]:
        """Get session with all relationships loaded."""
        return self.db.query(Session).options(
            joinedload(Session.course),
            joinedload(Session.attendance_records)
        ).filter(
            Session.id == session_id,
            Session.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # SPECIALIZED QUERIES
    # ============================================================
    
    def get_next_session(self, course_id: int) -> Optional[Session]:
        """Get the next upcoming session for a course."""
        return self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.date_time > datetime.utcnow(),
            Session.status == SessionStatus.UPCOMING,
            Session.deleted_at.is_(None)
        ).order_by(Session.date_time).first()
    
    def get_teacher_sessions(self, teacher_id: int) -> List[Session]:
        """Get all sessions for courses taught by a teacher."""
        return self.db.query(Session).join(Course).filter(
            Course.teacher_id == teacher_id,
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).order_by(Session.date_time).all()
    
    def get_teacher_upcoming_sessions(self, teacher_id: int) -> List[Session]:
        """Get upcoming sessions for a teacher."""
        return self.db.query(Session).join(Course).filter(
            Course.teacher_id == teacher_id,
            Session.date_time > datetime.utcnow(),
            Session.status == SessionStatus.UPCOMING,
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).order_by(Session.date_time).all()
    
    def get_student_sessions(self, student_id: int) -> List[Session]:
        """Get all sessions for courses a student is enrolled in."""
        return self.db.query(Session).join(Course).join(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == 'active',
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None),
            Enrollment.deleted_at.is_(None)
        ).order_by(Session.date_time).all()
    
    def get_student_upcoming_sessions(self, student_id: int) -> List[Session]:
        """Get upcoming sessions for a student."""
        return self.db.query(Session).join(Course).join(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == 'active',
            Session.date_time > datetime.utcnow(),
            Session.status == SessionStatus.UPCOMING,
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None),
            Enrollment.deleted_at.is_(None)
        ).order_by(Session.date_time).all()
    
    # ============================================================
    # ⭐ MISSED SESSIONS (CRITICAL)
    # ============================================================
    
    def get_missed_sessions(self, student_id: int) -> List[dict]:
        """
        Get missed sessions for a student.
        Used for the dashboard 'Missed Sessions' widget.
        """
        # Get all attendance records with status 'missed' for this student
        results = self.db.query(
            Session.id,
            Session.session_number,
            Session.title,
            Session.date_time,
            Session.recording_url,
            Session.recording_available,
            Course.id.label('course_id'),
            Course.title.label('course_title'),
            Course.slug.label('course_slug'),
            Attendance.watched_percentage,
            Attendance.status.label('attendance_status')
        ).join(Course).join(Enrollment).join(Attendance).filter(
            Enrollment.student_id == student_id,
            Attendance.status == AttendanceStatus.MISSED,
            Enrollment.status == 'active',
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None),
            Enrollment.deleted_at.is_(None)
        ).order_by(Session.date_time.desc()).all()
        
        return [
            {
                'session_id': r.id,
                'session_number': r.session_number,
                'session_title': r.title,
                'session_date': r.date_time,
                'course_id': r.course_id,
                'course_title': r.course_title,
                'course_slug': r.course_slug,
                'recording_url': r.recording_url,
                'recording_available': r.recording_available,
                'watched_percentage': r.watched_percentage,
                'can_makeup': r.recording_available and r.recording_url is not None,
                'status': r.attendance_status,
                'days_ago': (datetime.utcnow() - r.date_time).days
            }
            for r in results
        ]
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def update_recording(self, session_id: int, recording_url: str) -> Session:
        """Update recording URL for a session."""
        session = self.get_by_id_or_fail(session_id)
        session.recording_url = recording_url
        session.recording_available = True
        session.recording_processed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def mark_completed(self, session_id: int) -> Session:
        """Mark session as completed."""
        session = self.get_by_id_or_fail(session_id)
        session.status = SessionStatus.COMPLETED
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def mark_live(self, session_id: int) -> Session:
        """Mark session as live."""
        session = self.get_by_id_or_fail(session_id)
        session.status = SessionStatus.LIVE
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def cancel_session(self, session_id: int) -> Session:
        """Cancel a session."""
        session = self.get_by_id_or_fail(session_id)
        session.status = SessionStatus.CANCELLED
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_zoom_meeting(self, session_id: int, meeting_data: dict) -> Session:
        """Update Zoom meeting details for a session."""
        session = self.get_by_id_or_fail(session_id)
        
        if 'zoom_meeting_id' in meeting_data:
            session.zoom_meeting_id = meeting_data['zoom_meeting_id']
        if 'zoom_join_url' in meeting_data:
            session.zoom_join_url = meeting_data['zoom_join_url']
        if 'zoom_start_url' in meeting_data:
            session.zoom_start_url = meeting_data['zoom_start_url']
        if 'zoom_password' in meeting_data:
            session.zoom_password = meeting_data['zoom_password']
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    # ============================================================
    # COUNT OPERATIONS
    # ============================================================
    
    def count_by_course(self, course_id: int) -> int:
        """Count sessions for a course."""
        return self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.deleted_at.is_(None)
        ).count()
    
    def count_completed_by_student(self, student_id: int) -> int:
        """Count completed sessions for a student."""
        return self.db.query(Session).join(Course).join(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == 'active',
            Session.status == SessionStatus.COMPLETED,
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None),
            Enrollment.deleted_at.is_(None)
        ).count()
    
    def count_upcoming_by_student(self, student_id: int) -> int:
        """Count upcoming sessions for a student."""
        return self.db.query(Session).join(Course).join(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == 'active',
            Session.date_time > datetime.utcnow(),
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None),
            Enrollment.deleted_at.is_(None)
        ).count()
    
    def get_stats_by_course(self, course_id: int) -> dict:
        """Get session statistics for a course."""
        total = self.count_by_course(course_id)
        upcoming = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.status == SessionStatus.UPCOMING,
            Session.deleted_at.is_(None)
        ).count()
        completed = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.status == SessionStatus.COMPLETED,
            Session.deleted_at.is_(None)
        ).count()
        live = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.status == SessionStatus.LIVE,
            Session.deleted_at.is_(None)
        ).count()
        cancelled = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.status == SessionStatus.CANCELLED,
            Session.deleted_at.is_(None)
        ).count()
        
        return {
            "total": total,
            "upcoming": upcoming,
            "completed": completed,
            "live": live,
            "cancelled": cancelled,
        }
    
    # ============================================================
    # BULK OPERATIONS
    # ============================================================
    
    def bulk_create(self, sessions_data: List[dict]) -> List[Session]:
        """Create multiple sessions at once."""
        sessions = []
        for data in sessions_data:
            # Ensure session number is unique per course
            existing = self.db.query(Session).filter(
                Session.course_id == data.get('course_id'),
                Session.session_number == data.get('session_number'),
                Session.deleted_at.is_(None)
            ).first()
            
            if existing:
                raise ValueError(f"Session number {data.get('session_number')} already exists for this course")
            
            session = Session(**data)
            self.db.add(session)
            sessions.append(session)
        
        self.db.commit()
        for session in sessions:
            self.db.refresh(session)
        
        return sessions
    
    def bulk_delete_by_course(self, course_id: int) -> int:
        """Soft delete all sessions for a course."""
        sessions = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.deleted_at.is_(None)
        ).all()
        
        count = 0
        for session in sessions:
            self.soft_delete(session.id)
            count += 1
        
        return count