# ============================================================
# AETHER LINK - ATTENDANCE SERVICE ⭐ CRITICAL
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..repositories.attendance_repository import AttendanceRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.user_repository import UserRepository
from ..repositories.course_repository import CourseRepository
from ..models.attendance import AttendanceStatus
from ..models.enrollment import EnrollmentStatus
from ..models.user import UserRole


class AttendanceService:
    """Service for attendance business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.session_repo = SessionRepository(db)
        self.user_repo = UserRepository(db)
        self.course_repo = CourseRepository(db)
    
    # ============================================================
    # MARK ATTENDANCE
    # ============================================================
    
    def mark_present(
        self, 
        enrollment_id: int, 
        session_id: int,
        verified_by: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a student as present.
        
        Args:
            enrollment_id: Enrollment ID
            session_id: Session ID
            verified_by: Admin/teacher who verified
            remarks: Optional remarks
            
        Returns:
            Attendance record
            
        Raises:
            ValueError: If enrollment or session not found
        """
        # Check enrollment exists
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Student is not actively enrolled")
        
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check if session is in the past
        if session.date_time > datetime.utcnow():
            raise ValueError("Cannot mark attendance for future session")
        
        # Mark present
        attendance = self.attendance_repo.mark_present(
            enrollment_id=enrollment_id,
            session_id=session_id,
            verified_by=verified_by,
            remarks=remarks
        )
        
        return {
            "id": attendance.id,
            "enrollment_id": attendance.enrollment_id,
            "session_id": attendance.session_id,
            "status": attendance.status.value,
            "student_name": enrollment.student.full_name if enrollment.student else None,
            "session_title": session.title,
            "remarks": attendance.remarks,
        }
    
    def mark_missed(
        self, 
        enrollment_id: int, 
        session_id: int,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a student as missed.
        
        Args:
            enrollment_id: Enrollment ID
            session_id: Session ID
            remarks: Optional remarks
            
        Returns:
            Attendance record
            
        Raises:
            ValueError: If enrollment or session not found
        """
        # Check enrollment exists
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Student is not actively enrolled")
        
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Mark missed
        attendance = self.attendance_repo.mark_missed(
            enrollment_id=enrollment_id,
            session_id=session_id,
            remarks=remarks
        )
        
        return {
            "id": attendance.id,
            "enrollment_id": attendance.enrollment_id,
            "session_id": attendance.session_id,
            "status": attendance.status.value,
            "student_name": enrollment.student.full_name if enrollment.student else None,
            "session_title": session.title,
            "remarks": attendance.remarks,
        }
    
    def mark_excused(
        self, 
        enrollment_id: int, 
        session_id: int,
        verified_by: int,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a student as excused.
        
        Args:
            enrollment_id: Enrollment ID
            session_id: Session ID
            verified_by: Admin/teacher who verified
            remarks: Optional remarks
            
        Returns:
            Attendance record
            
        Raises:
            ValueError: If enrollment or session not found
        """
        # Check enrollment exists
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Student is not actively enrolled")
        
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Mark excused
        attendance = self.attendance_repo.mark_excused(
            enrollment_id=enrollment_id,
            session_id=session_id,
            verified_by=verified_by,
            remarks=remarks
        )
        
        return {
            "id": attendance.id,
            "enrollment_id": attendance.enrollment_id,
            "session_id": attendance.session_id,
            "status": attendance.status.value,
            "student_name": enrollment.student.full_name if enrollment.student else None,
            "session_title": session.title,
            "remarks": attendance.remarks,
            "verified_by": verified_by,
        }
    
    # ============================================================
    # ⭐ WATCH RECORDING (AUTO-MADE-UP)
    # ============================================================
    
    def watch_recording(
        self, 
        enrollment_id: int, 
        session_id: int, 
        watched_percentage: int
    ) -> Dict[str, Any]:
        """
        Student watches recording.
        Auto-marks as MADE_UP if watched_percentage >= 80%.
        
        Args:
            enrollment_id: Enrollment ID
            session_id: Session ID
            watched_percentage: Percentage of recording watched (0-100)
            
        Returns:
            Updated attendance record
            
        Raises:
            ValueError: If enrollment or session not found
        """
        # Check enrollment exists
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Student is not actively enrolled")
        
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check recording is available
        if not session.recording_available or not session.recording_url:
            raise ValueError("Recording is not available for this session")
        
        # Validate percentage
        if watched_percentage < 0 or watched_percentage > 100:
            raise ValueError("Watched percentage must be between 0 and 100")
        
        # Watch recording
        result = self.attendance_repo.watch_recording(
            enrollment_id=enrollment_id,
            session_id=session_id,
            watched_percentage=watched_percentage
        )
        
        return {
            "id": result["id"],
            "enrollment_id": result["enrollment_id"],
            "session_id": result["session_id"],
            "status": result["status"],
            "watched_percentage": result["watched_percentage"],
            "made_up": result["made_up"],
            "made_up_at": result["made_up_at"],
            "student_name": enrollment.student.full_name if enrollment.student else None,
            "session_title": session.title,
            "recording_url": session.recording_url,
        }
    
    # ============================================================
    # ⭐ SYNC ZOOM ATTENDANCE
    # ============================================================
    
    def sync_zoom_attendance(
        self, 
        session_id: int, 
        participant_emails: List[str],
        min_attendance_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Sync attendance from Zoom participant list.
        
        Args:
            session_id: Session ID
            participant_emails: List of participant emails from Zoom
            min_attendance_minutes: Minimum minutes to be considered present
            
        Returns:
            Sync results
            
        Raises:
            ValueError: If session not found
        """
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check if session is completed
        # We can sync attendance even if not completed
        
        # Sync attendance
        result = self.attendance_repo.sync_zoom_attendance(
            session_id=session_id,
            participant_emails=participant_emails,
            min_attendance_minutes=min_attendance_minutes
        )
        
        # Get enrolled students details
        enrollments = self.enrollment_repo.get_active_by_course(session.course_id)
        
        return {
            **result,
            "session_title": session.title,
            "course_id": session.course_id,
            "total_enrolled": len(enrollments),
            "attendance_rate": round(
                result["present_count"] / len(enrollments) * 100, 2
            ) if enrollments else 0,
        }
    
    # ============================================================
    # ⭐ GET MISSED SESSIONS
    # ============================================================
    
    def get_missed_sessions(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all missed sessions for a student.
        Powers the 'Missed Sessions' widget on student dashboard.
        
        Args:
            student_id: Student ID
            
        Returns:
            List of missed sessions
        """
        return self.attendance_repo.get_missed_by_student(student_id)
    
    def get_missed_sessions_by_course(
        self, 
        course_id: int, 
        student_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get missed sessions for a specific course.
        
        Args:
            course_id: Course ID
            student_id: Optional student filter
            
        Returns:
            List of missed sessions
        """
        return self.attendance_repo.get_missed_by_course(course_id, student_id)
    
    # ============================================================
    # GET ATTENDANCE SUMMARY
    # ============================================================
    
    def get_attendance_summary(self, student_id: int) -> Dict[str, Any]:
        """
        Get attendance summary for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            Attendance summary
        """
        return self.attendance_repo.get_student_attendance_summary(student_id)
    
    def get_session_attendance(self, session_id: int, teacher_id: int) -> Dict[str, Any]:
        """
        Get attendance summary for a session (teacher view).
        
        Args:
            session_id: Session ID
            teacher_id: Teacher ID (for permission check)
            
        Returns:
            Session attendance summary
            
        Raises:
            ValueError: If permission denied
        """
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check permission
        course = self.course_repo.get_by_id(session.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != teacher_id:
            teacher = self.user_repo.get_by_id(teacher_id)
            if not teacher or teacher.role != UserRole.ADMIN:
                raise ValueError("You don't have permission to view this session's attendance")
        
        return self.attendance_repo.get_session_attendance_summary(session_id)
    
    def get_enrollment_attendance_stats(self, enrollment_id: int) -> Dict[str, Any]:
        """
        Get attendance statistics for a specific enrollment.
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Attendance statistics
        """
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        return self.attendance_repo.get_attendance_stats(enrollment_id)
    
    # ============================================================
    # BULK ATTENDANCE MARKING
    # ============================================================
    
    def bulk_mark_attendance(
        self, 
        session_id: int, 
        present_student_ids: List[int],
        excused_student_ids: Optional[List[int]] = None,
        teacher_id: int = None
    ) -> Dict[str, Any]:
        """
        Bulk mark attendance for multiple students.
        
        Args:
            session_id: Session ID
            present_student_ids: List of student IDs present
            excused_student_ids: List of student IDs excused
            teacher_id: Teacher ID (for permission check)
            
        Returns:
            Marking results
            
        Raises:
            ValueError: If validation fails
        """
        # Check session exists
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check permission if teacher_id provided
        if teacher_id:
            course = self.course_repo.get_by_id(session.course_id)
            if course and course.teacher_id != teacher_id:
                teacher = self.user_repo.get_by_id(teacher_id)
                if not teacher or teacher.role != UserRole.ADMIN:
                    raise ValueError("You don't have permission to mark attendance for this session")
        
        # Bulk mark
        result = self.attendance_repo.bulk_mark_attendance(
            session_id=session_id,
            present_student_ids=present_student_ids,
            excused_student_ids=excused_student_ids,
        )
        
        return result
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_overall_attendance_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get overall attendance statistics for a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            Attendance statistics
        """
        # Get all enrollments for the course
        enrollments = self.enrollment_repo.get_active_by_course(course_id)
        
        total_students = len(enrollments)
        total_present = 0
        total_missed = 0
        total_made_up = 0
        total_excused = 0
        
        for enrollment in enrollments:
            stats = self.attendance_repo.get_attendance_stats(enrollment.id)
            total_present += stats["present"]
            total_missed += stats["missed"]
            total_made_up += stats["made_up"]
            total_excused += stats["excused"]
        
        total_attendance = total_present + total_made_up
        total_sessions = total_present + total_missed + total_made_up + total_excused
        
        return {
            "total_students": total_students,
            "total_present": total_present,
            "total_missed": total_missed,
            "total_made_up": total_made_up,
            "total_excused": total_excused,
            "total_sessions": total_sessions,
            "overall_attendance_rate": round(
                total_attendance / total_sessions * 100, 2
            ) if total_sessions > 0 else 0,
            "average_attendance_per_student": round(
                total_attendance / total_students, 2
            ) if total_students > 0 else 0,
        }