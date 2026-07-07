# ============================================================
# AETHER LINK - ZOOM SERVICE
# ============================================================

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from ..core.zoom import ZoomClient
from ..repositories.session_repository import SessionRepository
from ..repositories.attendance_repository import AttendanceRepository
from ..repositories.enrollment_repository import EnrollmentRepository

logger = logging.getLogger(__name__)


class ZoomService:
    """Service for Zoom integration business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.zoom_client = ZoomClient()
        self.session_repo = SessionRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    # ============================================================
    # MEETING MANAGEMENT
    # ============================================================

    async def create_meeting_for_session(
        self,
        session_id: int,
        topic: str,
        start_time: datetime,
        duration: int,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Zoom meeting for a session.
        
        Args:
            session_id: Session ID
            topic: Meeting topic
            start_time: Start time
            duration: Duration in minutes
            description: Meeting description
            
        Returns:
            Meeting details
            
        Raises:
            ValueError: If session not found or Zoom fails
        """
        # Get session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        # Check if meeting already exists
        if session.zoom_meeting_id:
            logger.info(f"Session {session_id} already has Zoom meeting {session.zoom_meeting_id}")
            return {
                "meeting_id": session.zoom_meeting_id,
                "join_url": session.zoom_join_url,
                "start_url": session.zoom_start_url,
            }

        # Create Zoom meeting
        try:
            result = await self.zoom_client.create_meeting(
                topic=topic[:200],
                start_time=start_time,
                duration=duration,
                agenda=description[:500] if description else "",
            )
            
            # Update session with Zoom details
            session.zoom_meeting_id = result["meeting_id"]
            session.zoom_join_url = result["join_url"]
            session.zoom_start_url = result["start_url"]
            session.zoom_password = result.get("password")
            
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"✅ Zoom meeting created for session {session_id}: {result['meeting_id']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to create Zoom meeting for session {session_id}: {e}")
            raise ValueError(f"Failed to create Zoom meeting: {str(e)}")

    async def get_meeting_details(self, session_id: int) -> Dict[str, Any]:
        """
        Get Zoom meeting details for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Meeting details
            
        Raises:
            ValueError: If session not found or no Zoom meeting
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if not session.zoom_meeting_id:
            raise ValueError("No Zoom meeting found for this session")

        try:
            result = await self.zoom_client.get_meeting(session.zoom_meeting_id)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get Zoom meeting for session {session_id}: {e}")
            raise ValueError(f"Failed to get Zoom meeting: {str(e)}")

    async def sync_attendance(self, session_id: int) -> Dict[str, Any]:
        """
        Sync attendance from Zoom participants.
        
        Args:
            session_id: Session ID
            
        Returns:
            Attendance sync results
            
        Raises:
            ValueError: If session not found or no Zoom meeting
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if not session.zoom_meeting_id:
            raise ValueError("No Zoom meeting found for this session")

        # Get participants from Zoom
        try:
            participants = await self.zoom_client.get_participants(
                session.zoom_meeting_id
            )
        except Exception as e:
            logger.error(f"❌ Failed to get Zoom participants for session {session_id}: {e}")
            raise ValueError(f"Failed to get Zoom participants: {str(e)}")

        if not participants:
            logger.warning(f"No participants found for session {session_id}")
            return {
                "session_id": session_id,
                "total_participants": 0,
                "marked_present": 0,
                "marked_missed": 0,
                "message": "No participants found in Zoom meeting",
            }

        # Get enrolled students
        enrollments = self.enrollment_repo.get_active_by_course(session.course_id)
        student_emails = {
            e.student.email.lower(): e.id 
            for e in enrollments 
            if e.student and e.student.email
        }

        # Match participants with students
        present_count = 0
        missed_count = 0
        missing_students = []

        for email, enrollment_id in student_emails.items():
            if email in [p.get("email", "").lower() for p in participants]:
                # Mark present
                self.attendance_repo.mark_present(enrollment_id, session_id)
                present_count += 1
            else:
                # Mark missed
                self.attendance_repo.mark_missed(enrollment_id, session_id)
                missed_count += 1
                missing_students.append(email)

        return {
            "session_id": session_id,
            "total_participants": len(participants),
            "total_students": len(student_emails),
            "marked_present": present_count,
            "marked_missed": missed_count,
            "missing_students": missing_students,
        }

    async def sync_recordings(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Sync recording URLs from Zoom.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of recordings
            
        Raises:
            ValueError: If session not found or no Zoom meeting
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if not session.zoom_meeting_id:
            raise ValueError("No Zoom meeting found for this session")

        try:
            recordings = await self.zoom_client.get_recordings(session.zoom_meeting_id)
            
            # Save recording URLs to session
            if recordings:
                recording_urls = [r["play_url"] for r in recordings if r.get("play_url")]
                if recording_urls:
                    session.zoom_recording_url = recording_urls[0]
                    session.zoom_recording_available = True
                    self.db.commit()
                    self.db.refresh(session)
            
            return recordings
            
        except Exception as e:
            logger.error(f"❌ Failed to sync recordings for session {session_id}: {e}")
            raise ValueError(f"Failed to sync recordings: {str(e)}")