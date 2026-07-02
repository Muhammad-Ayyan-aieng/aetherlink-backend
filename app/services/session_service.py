# ============================================================
# AETHER LINK - SESSION SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import html
import re

from ..repositories.session_repository import SessionRepository
from ..repositories.course_repository import CourseRepository
from ..repositories.user_repository import UserRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..models.sessions import Session, SessionStatus
from ..models.user import UserRole
from ..models.course import CourseStatus
from ..schemas.session import SessionCreate, SessionUpdate


class SessionService:
    """Service for session business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
    
    # ============================================================
    # CREATE
    # ============================================================
    
    def create_session(self, session_data: SessionCreate, user_id: int) -> Session:
        """
        Create a new session.
        
        Args:
            session_data: Session creation data
            user_id: User creating the session
            
        Returns:
            Created session
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check if course exists
        course = self.course_repo.get_by_id(session_data.course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Check permission (teacher or admin)
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to create sessions for this course")
        
        # Check if course is archived
        if course.status == CourseStatus.ARCHIVED:
            raise ValueError("Cannot add sessions to an archived course")
        
        # Check if session number already exists
        existing_sessions = self.session_repo.get_by_course(session_data.course_id)
        if any(s.session_number == session_data.session_number for s in existing_sessions):
            raise ValueError(f"Session number {session_data.session_number} already exists for this course")
        
        # Validate duration
        if session_data.duration_minutes < 1 or session_data.duration_minutes > 180:
            raise ValueError("Duration must be between 1 and 180 minutes")
        
        # Validate date (can be in the past for backfilling, but warn)
        # Allow past dates for administrative purposes
        
        # Sanitize input
        title = html.escape(session_data.title.strip())
        description = html.escape(session_data.description.strip()) if session_data.description else None
        
        if len(title) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        if description and len(description) > 5000:
            raise ValueError("Description must be less than 5000 characters")
        
        # Validate recording URL
        if session_data.recording_url and not session_data.recording_url.startswith(('http://', 'https://')):
            raise ValueError("Recording URL must be a valid URL")
        
        # Validate Zoom URL
        if session_data.zoom_join_url and not session_data.zoom_join_url.startswith(('http://', 'https://')):
            raise ValueError("Zoom join URL must be a valid URL")
        
        if session_data.zoom_join_url and 'zoom.us' not in session_data.zoom_join_url.lower():
            raise ValueError("Invalid Zoom URL")
        
        # Create session
        session = self.session_repo.create(
            course_id=session_data.course_id,
            session_number=session_data.session_number,
            title=title,
            description=description,
            date_time=session_data.date_time,
            duration_minutes=session_data.duration_minutes,
            zoom_meeting_id=session_data.zoom_meeting_id,
            zoom_join_url=session_data.zoom_join_url,
            zoom_start_url=session_data.zoom_start_url,
            zoom_password=session_data.zoom_password,
            recording_url=session_data.recording_url,
            status=session_data.status.value if session_data.status else SessionStatus.UPCOMING.value,
            meeting_notes=html.escape(session_data.meeting_notes.strip()) if session_data.meeting_notes else None,
            resources=session_data.resources,
        )
        
        # If recording URL is provided, mark as available
        if session_data.recording_url:
            session.recording_available = True
            session.recording_processed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        
        return session
    
    # ============================================================
    # READ
    # ============================================================
    
    def get_session(self, session_id: int) -> Session:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session
            
        Raises:
            ValueError: If session not found
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        return session
    
    def get_session_with_details(self, session_id: int) -> Session:
        """
        Get session with all details.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session with relationships
            
        Raises:
            ValueError: If session not found
        """
        session = self.session_repo.get_full_details(session_id)
        if not session:
            raise ValueError("Session not found")
        return session
    
    def get_sessions_by_course(
        self, 
        course_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get sessions for a course with pagination.
        
        Args:
            course_id: Course ID
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Sessions and total count
        """
        if limit > 100:
            limit = 100
        
        sessions, total = self.session_repo.get_by_course_paginated(course_id, skip, limit)
        
        return {
            "sessions": sessions,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    def get_upcoming_sessions(self, course_id: Optional[int] = None) -> List[Session]:
        """
        Get upcoming sessions.
        
        Args:
            course_id: Optional course filter
            
        Returns:
            List of upcoming sessions
        """
        return self.session_repo.get_upcoming(course_id)
    
    def get_today_sessions(self) -> List[Session]:
        """
        Get today's sessions.
        
        Returns:
            List of today's sessions
        """
        return self.session_repo.get_today_sessions()
    
    # ============================================================
    # STUDENT/TEACHER SESSIONS
    # ============================================================
    
    def get_student_sessions(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all sessions for a student's enrolled courses.
        
        Args:
            student_id: Student ID
            
        Returns:
            List of sessions with course info
        """
        sessions = self.session_repo.get_student_sessions(student_id)
        
        result = []
        for session in sessions:
            result.append({
                "id": session.id,
                "session_number": session.session_number,
                "title": session.title,
                "date_time": session.date_time,
                "duration_minutes": session.duration_minutes,
                "status": session.status.value,
                "zoom_join_url": session.zoom_join_url,
                "recording_url": session.recording_url,
                "recording_available": session.recording_available,
                "course_id": session.course_id,
                "course_title": session.course.title if session.course else None,
                "course_slug": session.course.slug if session.course else None,
            })
        
        return result
    
    def get_student_upcoming_sessions(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get upcoming sessions for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            List of upcoming sessions
        """
        sessions = self.session_repo.get_student_upcoming_sessions(student_id)
        
        result = []
        for session in sessions:
            result.append({
                "id": session.id,
                "session_number": session.session_number,
                "title": session.title,
                "date_time": session.date_time,
                "duration_minutes": session.duration_minutes,
                "zoom_join_url": session.zoom_join_url,
                "course_id": session.course_id,
                "course_title": session.course.title if session.course else None,
            })
        
        return result
    
    def get_teacher_sessions(self, teacher_id: int) -> List[Session]:
        """
        Get all sessions for a teacher's courses.
        
        Args:
            teacher_id: Teacher ID
            
        Returns:
            List of sessions
        """
        return self.session_repo.get_teacher_sessions(teacher_id)
    
    def get_teacher_upcoming_sessions(self, teacher_id: int) -> List[Session]:
        """
        Get upcoming sessions for a teacher.
        
        Args:
            teacher_id: Teacher ID
            
        Returns:
            List of upcoming sessions
        """
        return self.session_repo.get_teacher_upcoming_sessions(teacher_id)
    
    # ============================================================
    # UPDATE
    # ============================================================
    
    def update_session(self, session_id: int, update_data: SessionUpdate, user_id: int) -> Session:
        """
        Update a session.
        
        Args:
            session_id: Session ID
            update_data: Update data
            user_id: User making the update
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        session = self.session_repo.get_by_id_or_fail(session_id)
        
        # Check permission
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to update this session")
        
        # Validate updates
        update_dict = {}
        
        if update_data.session_number is not None:
            # Check if number already exists
            existing = self.session_repo.get_by_course(session.course_id)
            if any(s.session_number == update_data.session_number and s.id != session_id for s in existing):
                raise ValueError(f"Session number {update_data.session_number} already exists")
            update_dict["session_number"] = update_data.session_number
        
        if update_data.title is not None:
            title = html.escape(update_data.title.strip())
            if len(title) < 3:
                raise ValueError("Title must be at least 3 characters")
            update_dict["title"] = title
        
        if update_data.description is not None:
            update_dict["description"] = html.escape(update_data.description.strip()) if update_data.description else None
            if update_dict["description"] and len(update_dict["description"]) > 5000:
                raise ValueError("Description must be less than 5000 characters")
        
        if update_data.date_time is not None:
            update_dict["date_time"] = update_data.date_time
        
        if update_data.duration_minutes is not None:
            if update_data.duration_minutes < 1 or update_data.duration_minutes > 180:
                raise ValueError("Duration must be between 1 and 180 minutes")
            update_dict["duration_minutes"] = update_data.duration_minutes
        
        if update_data.zoom_meeting_id is not None:
            update_dict["zoom_meeting_id"] = update_data.zoom_meeting_id
        
        if update_data.zoom_join_url is not None:
            if update_data.zoom_join_url and 'zoom.us' not in update_data.zoom_join_url.lower():
                raise ValueError("Invalid Zoom URL")
            update_dict["zoom_join_url"] = update_data.zoom_join_url
        
        if update_data.zoom_start_url is not None:
            update_dict["zoom_start_url"] = update_data.zoom_start_url
        
        if update_data.zoom_password is not None:
            update_dict["zoom_password"] = update_data.zoom_password
        
        if update_data.recording_url is not None:
            if update_data.recording_url and not update_data.recording_url.startswith(('http://', 'https://')):
                raise ValueError("Recording URL must be a valid URL")
            update_dict["recording_url"] = update_data.recording_url
            if update_data.recording_url:
                update_dict["recording_available"] = True
                update_dict["recording_processed_at"] = datetime.utcnow()
            else:
                update_dict["recording_available"] = False
        
        if update_data.status is not None:
            update_dict["status"] = update_data.status.value
        
        if update_data.meeting_notes is not None:
            update_dict["meeting_notes"] = html.escape(update_data.meeting_notes.strip()) if update_data.meeting_notes else None
        
        if update_data.resources is not None:
            update_dict["resources"] = update_data.resources
        
        # Apply updates
        for key, value in update_dict.items():
            setattr(session, key, value)
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    # ============================================================
    # RECORDING MANAGEMENT
    # ============================================================
    
    def add_recording(self, session_id: int, recording_url: str, user_id: int) -> Session:
        """
        Add recording URL to a session.
        
        Args:
            session_id: Session ID
            recording_url: Recording URL
            user_id: User adding recording
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        session = self.session_repo.get_by_id_or_fail(session_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to add recordings to this session")
        
        if not recording_url.startswith(('http://', 'https://')):
            raise ValueError("Recording URL must be a valid URL")
        
        session.recording_url = recording_url
        session.recording_available = True
        session.recording_processed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def mark_completed(self, session_id: int, user_id: int) -> Session:
        """
        Mark session as completed.
        
        Args:
            session_id: Session ID
            user_id: User making the change
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        session = self.session_repo.get_by_id_or_fail(session_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to mark this session as completed")
        
        if session.status == SessionStatus.COMPLETED:
            raise ValueError("Session is already completed")
        
        # If session has recording, mark as available
        if session.recording_url and not session.recording_available:
            session.recording_available = True
            session.recording_processed_at = datetime.utcnow()
        
        session.status = SessionStatus.COMPLETED
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def mark_cancelled(self, session_id: int, user_id: int) -> Session:
        """
        Mark session as cancelled.
        
        Args:
            session_id: Session ID
            user_id: User making the change
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        session = self.session_repo.get_by_id_or_fail(session_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to cancel this session")
        
        if session.status == SessionStatus.CANCELLED:
            raise ValueError("Session is already cancelled")
        
        session.status = SessionStatus.CANCELLED
        self.db.commit()
        self.db.refresh(session)
        return session
    
    # ============================================================
    # DELETE / RESTORE
    # ============================================================
    
    def delete_session(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """
        Soft delete a session.
        
        Args:
            session_id: Session ID
            user_id: User making the deletion
            
        Returns:
            Success message
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        session = self.session_repo.get_by_id_or_fail(session_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to delete this session")
        
        self.session_repo.soft_delete(session_id)
        
        return {"message": "Session deleted successfully"}
    
    def restore_session(self, session_id: int, user_id: int) -> Session:
        """
        Restore a soft-deleted session.
        
        Args:
            session_id: Session ID
            user_id: User making the restore
            
        Returns:
            Restored session
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        session = self.session_repo.get_by_id(session_id, include_deleted=True)
        if not session:
            raise ValueError("Session not found")
        
        if session.deleted_at is None:
            raise ValueError("Session is not deleted")
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to restore this session")
        
        session.deleted_at = None
        self.db.commit()
        self.db.refresh(session)
        return session
    
    # ============================================================
    # ZOOM INTEGRATION
    # ============================================================
    
    def create_zoom_meeting(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """
        Create a Zoom meeting for a session.
        """
        # This is a placeholder. Actual Zoom API integration will be added later.
        # For now, just return a placeholder response.
        return {
            "message": "Zoom meeting creation will be implemented with Zoom API integration",
            "session_id": session_id,
            "zoom_meeting_id": "PLACEHOLDER",
            "zoom_join_url": "PLACEHOLDER",
            "zoom_start_url": "PLACEHOLDER",
        }
    
    def sync_zoom_attendance(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """
        Sync Zoom attendance for a session.
        """
        # This is a placeholder. Actual Zoom API integration will be added later.
        return {
            "message": "Zoom attendance sync will be implemented with Zoom API integration",
            "session_id": session_id,
        }
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_session_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get session statistics for a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            Session statistics
        """
        return self.session_repo.get_stats_by_course(course_id)