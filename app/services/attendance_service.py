# ============================================================
# AETHER LINK - ATTENDANCE SERVICE
# ============================================================

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import logging

from ..repositories.attendance_repository import AttendanceRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..repositories.user_repository import UserRepository
from ..repositories.course_repository import CourseRepository
from ..models.attendance import Attendance, AttendanceStatus
from ..models.sessions import SessionStatus
from ..models.user import UserRole
from ..models.enrollment import EnrollmentStatus
from ..schemas.attendance import AttendanceMark, BulkAttendanceMark, WatchRecording

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for attendance business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.session_repo = SessionRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.user_repo = UserRepository(db)
        self.course_repo = CourseRepository(db)
    
    # ============================================================
    # ATTENDANCE THRESHOLDS
    # ============================================================
    
    ATTENDANCE_THRESHOLD = 0.60  # 60% of session duration
    MADE_UP_THRESHOLD = 0.80     # 80% of recording watched
    
    # ============================================================
    # MANUAL MARK ATTENDANCE (Teacher)
    # ============================================================
    
    def mark_attendance(self, teacher_id: int, mark_data: AttendanceMark) -> Dict[str, Any]:
        """
        Mark attendance for a student in a session (teacher only).
        
        Args:
            teacher_id: Teacher ID
            mark_data: Attendance mark data
            
        Returns:
            Updated attendance record
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Get session
        session = self.session_repo.get_by_id(mark_data.session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check if session is in the past (can mark past sessions)
        if session.start_time > datetime.now(timezone.utc):
            raise ValueError("Cannot mark attendance for future sessions")
        
        # Check teacher permission
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != teacher_id:
            teacher = self.user_repo.get_by_id(teacher_id)
            if not teacher or teacher.role != UserRole.ADMIN:
                raise ValueError("You don't have permission to mark attendance for this session")
        
        # Check if student is enrolled
        enrollment = self.enrollment_repo.get_active_by_student_and_course(
            mark_data.student_id, 
            session.course_id
        )
        if not enrollment:
            raise ValueError("Student is not enrolled in this course")
        
        # Check if attendance already exists
        existing = self.attendance_repo.get_by_enrollment_and_session(
            enrollment.id,
            mark_data.session_id
        )
        
        if existing:
            # Update existing
            existing.status = AttendanceStatus(mark_data.status)
            existing.marked_by = teacher_id
            existing.marked_at = datetime.now(timezone.utc)
            existing.auto_marked = False
            self.db.commit()
            self.db.refresh(existing)
            return self._format_attendance_response(existing)
        
        # Create new attendance
        attendance = self.attendance_repo.create(
            enrollment_id=enrollment.id,
            session_id=mark_data.session_id,
            status=AttendanceStatus(mark_data.status),
            marked_by=teacher_id,
            marked_at=datetime.now(timezone.utc),
            auto_marked=False,
        )
        
        self.db.commit()
        self.db.refresh(attendance)
        return self._format_attendance_response(attendance)
    
    # ============================================================
    # BULK MARK ATTENDANCE (Teacher)
    # ============================================================
    
    def bulk_mark_attendance(self, teacher_id: int, bulk_data: BulkAttendanceMark) -> Dict[str, Any]:
        """
        Bulk mark attendance for multiple students in a session.
        
        Args:
            teacher_id: Teacher ID
            bulk_data: Bulk attendance data
            
        Returns:
            List of updated attendance records
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Get session
        session = self.session_repo.get_by_id(bulk_data.session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check teacher permission
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != teacher_id:
            teacher = self.user_repo.get_by_id(teacher_id)
            if not teacher or teacher.role != UserRole.ADMIN:
                raise ValueError("You don't have permission to mark attendance for this session")
        
        # Get all enrolled students
        enrollments = self.enrollment_repo.get_active_by_course(session.course_id)
        enrolled_student_ids = [e.student_id for e in enrollments]
        
        results = []
        for mark in bulk_data.attendance_list:
            # Skip if student not enrolled
            if mark.student_id not in enrolled_student_ids:
                continue
            
            try:
                result = self.mark_attendance(
                    teacher_id=teacher_id,
                    mark_data=AttendanceMark(
                        student_id=mark.student_id,
                        session_id=bulk_data.session_id,
                        status=mark.status
                    )
                )
                results.append(result)
            except ValueError as e:
                logger.warning(f"Failed to mark attendance for student {mark.student_id}: {e}")
                continue
        
        return {
            "session_id": bulk_data.session_id,
            "total_marked": len(results),
            "attendance": results
        }
    
    # ============================================================
    # AUTO MARK ATTENDANCE (Zoom/BBB Webhook)
    # ============================================================
    
    def auto_mark_attendance(
        self,
        session_id: int,
        participant_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Auto-mark attendance from Zoom/BBB webhook.
        
        Args:
            session_id: Session ID
            participant_data: List of participant data with:
                - student_id: int
                - join_time: datetime
                - leave_time: datetime
                - duration_minutes: int
                - email: str (fallback)
            
        Returns:
            Attendance summary
            
        Raises:
            ValueError: If session not found
        """
        # Get session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Calculate session duration
        if session.duration_minutes:
            session_duration = session.duration_minutes
        else:
            # Calculate from start and end time
            if session.end_time and session.start_time:
                session_duration = (session.end_time - session.start_time).total_seconds() / 60
            else:
                session_duration = 60  # Default 1 hour
        
        results = []
        for participant in participant_data:
            # Try to find student by ID or email
            student = None
            if participant.get('student_id'):
                student = self.user_repo.get_by_id(participant['student_id'])
            
            if not student and participant.get('email'):
                student = self.user_repo.get_by_email(participant['email'])
            
            if not student:
                logger.warning(f"Student not found for participant: {participant}")
                continue
            
            # Check if student is enrolled
            enrollment = self.enrollment_repo.get_active_by_student_and_course(
                student.id, 
                session.course_id
            )
            if not enrollment:
                logger.warning(f"Student {student.id} not enrolled in course {session.course_id}")
                continue
            
            # Calculate attendance percentage
            duration_minutes = participant.get('duration_minutes', 0)
            if duration_minutes == 0 and participant.get('join_time') and participant.get('leave_time'):
                join_time = participant['join_time']
                leave_time = participant['leave_time']
                if isinstance(join_time, str):
                    join_time = datetime.fromisoformat(join_time.replace('Z', '+00:00'))
                if isinstance(leave_time, str):
                    leave_time = datetime.fromisoformat(leave_time.replace('Z', '+00:00'))
                duration_minutes = (leave_time - join_time).total_seconds() / 60
            
            attendance_percentage = duration_minutes / session_duration if session_duration > 0 else 0
            
            # Determine status based on attendance percentage
            if attendance_percentage >= self.ATTENDANCE_THRESHOLD:
                status = AttendanceStatus.PRESENT
            else:
                status = AttendanceStatus.MISSED
            
            # Check if attendance already exists
            existing = self.attendance_repo.get_by_enrollment_and_session(
                enrollment.id,
                session_id
            )
            
            if existing:
                # Update existing
                existing.status = status
                existing.join_time = participant.get('join_time')
                existing.leave_time = participant.get('leave_time')
                existing.duration_minutes = int(duration_minutes)
                existing.auto_marked = True
                existing.marked_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing)
                results.append(self._format_attendance_response(existing))
            else:
                # Create new
                attendance = self.attendance_repo.create(
                    enrollment_id=enrollment.id,
                    session_id=session_id,
                    status=status,
                    join_time=participant.get('join_time'),
                    leave_time=participant.get('leave_time'),
                    duration_minutes=int(duration_minutes),
                    auto_marked=True,
                    marked_at=datetime.now(timezone.utc),
                )
                self.db.commit()
                self.db.refresh(attendance)
                results.append(self._format_attendance_response(attendance))
        
        return {
            "session_id": session_id,
            "total_processed": len(participant_data),
            "total_marked": len(results),
            "attendance": results
        }
    
    # ============================================================
    # WATCH RECORDING & MARK AS MADE UP
    # ============================================================
    
    def mark_made_up(self, student_id: int, watch_data: WatchRecording) -> Dict[str, Any]:
        """
        Mark attendance as made up after watching recording.
        
        Args:
            student_id: Student ID
            watch_data: Watch recording data
            
        Returns:
            Updated attendance
            
        Raises:
            ValueError: If validation fails
        """
        # Get attendance record
        attendance = self.attendance_repo.get_by_id(watch_data.attendance_id)
        if not attendance:
            raise ValueError("Attendance record not found")
        
        # Check if student owns this attendance
        if attendance.student_id != student_id:
            raise ValueError("You don't have permission to update this attendance")
        
        # Check if already made up
        if attendance.status == AttendanceStatus.MADE_UP:
            raise ValueError("This session is already marked as made up")
        
        # Check if can be made up (only missed sessions can be made up)
        if attendance.status != AttendanceStatus.MISSED:
            raise ValueError("Only missed sessions can be made up")
        
        # Check watch percentage
        watch_percentage = watch_data.watch_percentage
        if watch_percentage < self.MADE_UP_THRESHOLD * 100:
            raise ValueError(
                f"You need to watch at least {int(self.MADE_UP_THRESHOLD * 100)}% "
                f"of the recording. Currently: {watch_percentage}%"
            )
        
        # Update attendance
        attendance.status = AttendanceStatus.MADE_UP
        attendance.watch_time_minutes = watch_data.watch_time_minutes
        attendance.watch_percentage = watch_percentage
        attendance.made_up_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(attendance)
        return self._format_attendance_response(attendance)
    
    # ============================================================
    # GET ATTENDANCE BY SESSION (Teacher)
    # ============================================================
    
    def get_session_attendance(self, session_id: int, teacher_id: int) -> Dict[str, Any]:
        """
        Get all attendance records for a session.
        
        Args:
            session_id: Session ID
            teacher_id: Teacher ID
            
        Returns:
            Attendance records
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Get session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check teacher permission
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != teacher_id:
            teacher = self.user_repo.get_by_id(teacher_id)
            if not teacher or teacher.role != UserRole.ADMIN:
                raise ValueError("You don't have permission to view this session's attendance")
        
        # Get attendance
        attendance = self.attendance_repo.get_by_session(session_id)
        
        # Calculate summary
        total = len(attendance)
        present = sum(1 for a in attendance if a.status == AttendanceStatus.PRESENT)
        missed = sum(1 for a in attendance if a.status == AttendanceStatus.MISSED)
        made_up = sum(1 for a in attendance if a.status == AttendanceStatus.MADE_UP)
        absent = sum(1 for a in attendance if a.status == AttendanceStatus.ABSENT)
        
        return {
            "session_id": session_id,
            "course_id": session.course_id,
            "total_students": total,
            "attendance": [self._format_attendance_response(a) for a in attendance],
            "summary": {
                "present": present,
                "absent": absent,
                "missed": missed,
                "made_up": made_up,
                "attendance_rate": round((present + made_up) / total * 100, 2) if total > 0 else 0
            }
        }
    
    # ============================================================
    # GET STUDENT ATTENDANCE
    # ============================================================
    
    def get_student_attendance(
        self,
        student_id: int,
        requesting_user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get attendance records for a student.
        
        Args:
            student_id: Student ID
            requesting_user_id: User making the request
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Attendance records
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        if limit > 100:
            limit = 100
        
        # Check permission
        if student_id != requesting_user_id:
            requesting_user = self.user_repo.get_by_id(requesting_user_id)
            if not requesting_user or requesting_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
                raise ValueError("You don't have permission to view this student's attendance")
        
        # Check if student exists
        student = self.user_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        # Get attendance
        attendance, total = self.attendance_repo.get_by_student_paginated(student_id, skip, limit)
        
        # Calculate summary
        total_attendance = len(attendance)
        present = sum(1 for a in attendance if a.status == AttendanceStatus.PRESENT)
        missed = sum(1 for a in attendance if a.status == AttendanceStatus.MISSED)
        made_up = sum(1 for a in attendance if a.status == AttendanceStatus.MADE_UP)
        absent = sum(1 for a in attendance if a.status == AttendanceStatus.ABSENT)
        
        return {
            "student_id": student_id,
            "student_name": student.full_name,
            "attendance": [self._format_attendance_response(a) for a in attendance],
            "total": total,
            "summary": {
                "present": present,
                "absent": absent,
                "missed": missed,
                "made_up": made_up,
                "attendance_rate": round((present + made_up) / total * 100, 2) if total > 0 else 0,
                "total_sessions": total
            },
            "pagination": {
                "page": skip // limit + 1 if limit > 0 else 1,
                "page_size": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0
            }
        }
    
    # ============================================================
    # GET STUDENT ATTENDANCE SUMMARY (Dashboard)
    # ============================================================
    
    def get_student_attendance_summary(self, student_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get attendance summary for a student.
        
        Args:
            student_id: Student ID
            course_id: Optional course filter
            
        Returns:
            Attendance summary
        """
        try:
            # Get all attendance for student
            if course_id:
                # Get sessions for course
                sessions = self.session_repo.get_by_course(course_id)
                session_ids = [s.id for s in sessions] if sessions else []
                if session_ids:
                    attendance = self.attendance_repo.get_by_student_and_sessions(student_id, session_ids)
                else:
                    attendance = []
            else:
                # Use get_by_student from repository
                attendance = self.attendance_repo.get_by_student(student_id)
            
            total = len(attendance)
            present = sum(1 for a in attendance if a.status == AttendanceStatus.PRESENT)
            missed = sum(1 for a in attendance if a.status == AttendanceStatus.MISSED)
            made_up = sum(1 for a in attendance if a.status == AttendanceStatus.MADE_UP)
            absent = sum(1 for a in attendance if a.status == AttendanceStatus.ABSENT)
            
            return {
                "student_id": student_id,
                "course_id": course_id,
                "total_sessions": total,
                "present": present,
                "absent": absent,
                "missed": missed,
                "made_up": made_up,
                "attendance_rate": round((present + made_up) / total * 100, 2) if total > 0 else 0,
                "missed_count": missed,
                "missed_can_be_made_up": missed > 0
            }
        except Exception as e:
            logger.error(f"Error getting attendance summary for student {student_id}: {e}")
            return {
                "student_id": student_id,
                "course_id": course_id,
                "total_sessions": 0,
                "present": 0,
                "absent": 0,
                "missed": 0,
                "made_up": 0,
                "attendance_rate": 0,
                "missed_count": 0,
                "missed_can_be_made_up": False
            }
    
    # ============================================================
    # GET MISSED SESSIONS (Student Dashboard)
    # ============================================================
    
    def get_missed_sessions(self, student_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get missed sessions for a student.
        
        Args:
            student_id: Student ID
            course_id: Optional course filter
            
        Returns:
            Missed sessions
        """
        try:
            # Use the repository's get_missed_by_student method
            if course_id:
                missed = self.attendance_repo.get_missed_by_course(course_id, student_id)
            else:
                missed = self.attendance_repo.get_missed_by_student(student_id)
            
            return {
                "student_id": student_id,
                "course_id": course_id,
                "missed_count": len(missed),
                "missed_sessions": missed
            }
        except Exception as e:
            logger.error(f"Error getting missed sessions for student {student_id}: {e}")
            return {
                "student_id": student_id,
                "course_id": course_id,
                "missed_count": 0,
                "missed_sessions": []
            }
    
    # ============================================================
    # COURSE ATTENDANCE SUMMARY (Teacher)
    # ============================================================
    
    def get_course_attendance_summary(self, course_id: int, teacher_id: int) -> Dict[str, Any]:
        """
        Get attendance summary for a course.
        
        Args:
            course_id: Course ID
            teacher_id: Teacher ID
            
        Returns:
            Attendance summary
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check course exists
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Check teacher permission
        if course.teacher_id != teacher_id:
            teacher = self.user_repo.get_by_id(teacher_id)
            if not teacher or teacher.role != UserRole.ADMIN:
                raise ValueError("You don't have permission to view this course's attendance")
        
        # Get all sessions for course
        sessions = self.session_repo.get_by_course(course_id)
        session_ids = [s.id for s in sessions] if sessions else []
        
        # Get all enrollments
        enrollments = self.enrollment_repo.get_active_by_course(course_id)
        
        # Get attendance for all sessions
        all_attendance = []
        for session_id in session_ids:
            attendance = self.attendance_repo.get_by_session(session_id)
            all_attendance.extend(attendance)
        
        # Calculate per-student summary
        student_summary = []
        for enrollment in enrollments:
            student = enrollment.student
            student_attendance = [a for a in all_attendance if a.enrollment_id == enrollment.id]
            total = len(student_attendance)
            present = sum(1 for a in student_attendance if a.status == AttendanceStatus.PRESENT)
            missed = sum(1 for a in student_attendance if a.status == AttendanceStatus.MISSED)
            made_up = sum(1 for a in student_attendance if a.status == AttendanceStatus.MADE_UP)
            
            student_summary.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "student_email": student.email,
                "total_sessions": total,
                "present": present,
                "missed": missed,
                "made_up": made_up,
                "attendance_rate": round((present + made_up) / total * 100, 2) if total > 0 else 0
            })
        
        return {
            "course_id": course_id,
            "course_title": course.title,
            "total_students": len(enrollments),
            "total_sessions": len(sessions),
            "students": student_summary
        }
    
    def get_student_attendance_summary(self, student_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get attendance summary for a student.
        """
        try:
            if course_id:
                sessions = self.session_repo.get_by_course(course_id)
                session_ids = [s.id for s in sessions] if sessions else []
                if session_ids:
                    attendance = self.attendance_repo.get_by_student_and_sessions(student_id, session_ids)
                else:
                    attendance = []
            else:
                attendance = self.attendance_repo.get_by_student(student_id)
            
            total = len(attendance)
            present = sum(1 for a in attendance if a.status == AttendanceStatus.PRESENT)
            missed = sum(1 for a in attendance if a.status == AttendanceStatus.MISSED)
            made_up = sum(1 for a in attendance if a.status == AttendanceStatus.MADE_UP)
            absent = sum(1 for a in attendance if a.status == AttendanceStatus.ABSENT)
            excused = sum(1 for a in attendance if a.status == AttendanceStatus.EXCUSED)
            
            attendance_rate = round((present + made_up) / total * 100, 2) if total > 0 else 0
            
            return {
                "student_id": student_id,
                "course_id": course_id,
                "total_sessions": total,
                "present": present,
                "absent": absent,
                "missed": missed,
                "made_up": made_up,
                "excused": excused,
                "attendance_rate": attendance_rate,
                "attendance_percentage": attendance_rate,  # For compatibility
                "missed_count": missed,
                "missed_can_be_made_up": missed > 0
            }
        except Exception as e:
            logger.error(f"Error getting attendance summary for student {student_id}: {e}")
            return {
                "student_id": student_id,
                "course_id": course_id,
                "total_sessions": 0,
                "present": 0,
                "absent": 0,
                "missed": 0,
                "made_up": 0,
                "excused": 0,
                "attendance_rate": 0,
                "attendance_percentage": 0,
                "missed_count": 0,
                "missed_can_be_made_up": False
            }
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _format_attendance_response(self, attendance: Attendance) -> Dict[str, Any]:
        """Format attendance for API response."""
        return {
            "id": attendance.id,
            "enrollment_id": attendance.enrollment_id,
            "session_id": attendance.session_id,
            "status": attendance.status.value,
            "join_time": attendance.join_time,
            "leave_time": attendance.leave_time,
            "duration_minutes": attendance.duration_minutes,
            "watch_time_minutes": attendance.watch_time_minutes,
            "watch_percentage": attendance.watch_percentage,
            "auto_marked": attendance.auto_marked,
            "marked_by": attendance.marked_by,
            "marked_at": attendance.marked_at,
            "made_up_at": attendance.made_up_at,
            "created_at": attendance.created_at,
            "updated_at": attendance.updated_at,
        }
    