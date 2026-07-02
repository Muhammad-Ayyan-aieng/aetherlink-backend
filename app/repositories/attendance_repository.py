# ============================================================
# AETHER LINK - ATTENDANCE REPOSITORY ⭐ CRITICAL
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from .base import BaseRepository
from ..models.attendance import Attendance, AttendanceStatus
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.sessions import Session, SessionStatus
from ..models.user import User
from ..models.course import Course


class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for Attendance model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Attendance)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_enrollment(self, enrollment_id: int) -> List[Attendance]:
        """Get all attendance records for an enrollment."""
        return self.db.query(Attendance).filter(
            Attendance.enrollment_id == enrollment_id
        ).order_by(Attendance.created_at).all()
    
    def get_by_session(self, session_id: int) -> List[Attendance]:
        """Get all attendance records for a session."""
        return self.db.query(Attendance).filter(
            Attendance.session_id == session_id
        ).all()
    
    def get_by_enrollment_and_session(
        self, 
        enrollment_id: int, 
        session_id: int
    ) -> Optional[Attendance]:
        """Get specific attendance record by enrollment and session."""
        return self.db.query(Attendance).filter(
            Attendance.enrollment_id == enrollment_id,
            Attendance.session_id == session_id
        ).first()
    
    def get_or_create(
        self, 
        enrollment_id: int, 
        session_id: int
    ) -> Attendance:
        """Get existing attendance record or create one."""
        attendance = self.get_by_enrollment_and_session(enrollment_id, session_id)
        if attendance is None:
            attendance = Attendance(
                enrollment_id=enrollment_id,
                session_id=session_id,
                status=AttendanceStatus.MISSED
            )
            self.db.add(attendance)
            self.db.commit()
            self.db.refresh(attendance)
        return attendance
    
    # ============================================================
    # ⭐ MISSED SESSIONS (CRITICAL)
    # ============================================================
    
    def get_missed_by_student(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all missed sessions for a student.
        Powers the 'Missed Sessions' widget on student dashboard.
        """
        results = self.db.query(
            Attendance.id,
            Attendance.status,
            Attendance.watched_recording,
            Attendance.watched_percentage,
            Attendance.made_up_at,
            Session.id.label('session_id'),
            Session.session_number,
            Session.title.label('session_title'),
            Session.date_time,
            Session.recording_url,
            Session.recording_available,
            Course.id.label('course_id'),
            Course.title.label('course_title'),
            Course.slug.label('course_slug'),
            Enrollment.id.label('enrollment_id')
        ).join(Session).join(Enrollment).join(Course).filter(
            Enrollment.student_id == student_id,
            Attendance.status == AttendanceStatus.MISSED,
            Enrollment.deleted_at.is_(None),
            Session.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).order_by(Session.date_time.desc()).all()
        
        return [
            {
                'id': r.id,
                'session_id': r.session_id,
                'session_number': r.session_number,
                'session_title': r.session_title,
                'session_date': r.date_time,
                'course_id': r.course_id,
                'course_title': r.course_title,
                'course_slug': r.course_slug,
                'enrollment_id': r.enrollment_id,
                'recording_url': r.recording_url,
                'recording_available': r.recording_available,
                'watched_percentage': r.watched_percentage,
                'watched_recording': r.watched_recording,
                'can_makeup': r.recording_available and r.recording_url is not None,
                'days_ago': (datetime.utcnow() - r.date_time).days,
                'made_up_at': r.made_up_at,
                'status': r.status
            }
            for r in results
        ]
    
    def get_missed_by_course(self, course_id: int, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get missed sessions for a specific course."""
        query = self.db.query(
            Attendance.id,
            Attendance.status,
            Attendance.watched_percentage,
            Session.id.label('session_id'),
            Session.session_number,
            Session.title.label('session_title'),
            Session.date_time,
            Session.recording_url,
            Session.recording_available,
            Enrollment.student_id,
            User.full_name.label('student_name'),
            User.email.label('student_email')
        ).join(Session).join(Enrollment).join(User).filter(
            Session.course_id == course_id,
            Attendance.status == AttendanceStatus.MISSED,
            Enrollment.deleted_at.is_(None),
            Session.deleted_at.is_(None)
        )
        
        if student_id:
            query = query.filter(Enrollment.student_id == student_id)
        
        results = query.order_by(Session.date_time.desc()).all()
        
        return [
            {
                'id': r.id,
                'session_id': r.session_id,
                'session_number': r.session_number,
                'session_title': r.session_title,
                'session_date': r.date_time,
                'student_id': r.student_id,
                'student_name': r.student_name,
                'student_email': r.student_email,
                'recording_url': r.recording_url,
                'recording_available': r.recording_available,
                'watched_percentage': r.watched_percentage,
                'can_makeup': r.recording_available and r.recording_url is not None,
                'days_ago': (datetime.utcnow() - r.date_time).days,
                'status': r.status
            }
            for r in results
        ]
    
    def get_present_by_student(self, student_id: int) -> List[Attendance]:
        """Get present sessions for a student."""
        return self.db.query(Attendance).join(Enrollment).filter(
            Enrollment.student_id == student_id,
            Attendance.status == AttendanceStatus.PRESENT,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    def get_made_up_by_student(self, student_id: int) -> List[Attendance]:
        """Get made-up sessions for a student."""
        return self.db.query(Attendance).join(Enrollment).filter(
            Enrollment.student_id == student_id,
            Attendance.status == AttendanceStatus.MADE_UP,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def mark_present(
        self, 
        enrollment_id: int, 
        session_id: int, 
        verified_by: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> Attendance:
        """Mark a student as present."""
        attendance = self.get_or_create(enrollment_id, session_id)
        attendance.status = AttendanceStatus.PRESENT
        if verified_by:
            attendance.verified_by = verified_by
            attendance.verified_at = datetime.utcnow()
        if remarks:
            attendance.remarks = remarks
        self.db.commit()
        self.db.refresh(attendance)
        return attendance
    
    def mark_missed(
        self, 
        enrollment_id: int, 
        session_id: int,
        remarks: Optional[str] = None
    ) -> Attendance:
        """Mark a student as missed."""
        attendance = self.get_or_create(enrollment_id, session_id)
        attendance.status = AttendanceStatus.MISSED
        if remarks:
            attendance.remarks = remarks
        self.db.commit()
        self.db.refresh(attendance)
        return attendance
    
    def mark_made_up(
        self, 
        enrollment_id: int, 
        session_id: int,
        method: str = "recording",
        notes: Optional[str] = None,
        verified_by: Optional[int] = None
    ) -> Attendance:
        """Mark a student as made up."""
        attendance = self.get_or_create(enrollment_id, session_id)
        attendance.status = AttendanceStatus.MADE_UP
        attendance.made_up_at = datetime.utcnow()
        attendance.makeup_method = method
        if notes:
            attendance.makeup_notes = notes
        if verified_by:
            attendance.verified_by = verified_by
            attendance.verified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attendance)
        return attendance
    
    def mark_excused(
        self, 
        enrollment_id: int, 
        session_id: int,
        verified_by: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> Attendance:
        """Mark a student as excused."""
        attendance = self.get_or_create(enrollment_id, session_id)
        attendance.status = AttendanceStatus.EXCUSED
        if verified_by:
            attendance.verified_by = verified_by
            attendance.verified_at = datetime.utcnow()
        if remarks:
            attendance.remarks = remarks
        self.db.commit()
        self.db.refresh(attendance)
        return attendance
    
    # ============================================================
    # ⭐ WATCH RECORDING (Auto-Made-Up)
    # ============================================================
    
    def watch_recording(
        self, 
        enrollment_id: int, 
        session_id: int, 
        watched_percentage: int
    ) -> Dict[str, Any]:
        """
        Update recording watch progress.
        Auto-marks as MADE_UP if watched_percentage >= 80%.
        """
        attendance = self.get_or_create(enrollment_id, session_id)
        
        # Update watch progress
        if watched_percentage < 0:
            watched_percentage = 0
        elif watched_percentage > 100:
            watched_percentage = 100
        
        attendance.watched_recording = True
        attendance.watched_percentage = watched_percentage
        attendance.last_watch_time = datetime.utcnow()
        
        # ⭐ AUTO-MADE-UP: If watched >= 80% and status is MISSED
        status_changed = False
        if watched_percentage >= 80 and attendance.status == AttendanceStatus.MISSED:
            attendance.status = AttendanceStatus.MADE_UP
            attendance.made_up_at = datetime.utcnow()
            attendance.makeup_method = "recording"
            status_changed = True
        
        self.db.commit()
        self.db.refresh(attendance)
        
        return {
            "id": attendance.id,
            "status": attendance.status,
            "watched_percentage": attendance.watched_percentage,
            "made_up": status_changed,
            "enrollment_id": attendance.enrollment_id,
            "session_id": attendance.session_id,
            "made_up_at": attendance.made_up_at,
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
        Participants are marked PRESENT, others are marked MISSED.
        """
        # Get all active enrollments for this course
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.course_id == session.course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).all()
        
        # Get student emails
        student_emails = {
            e.student.email.lower(): e.id 
            for e in enrollments 
            if e.student and e.student.email
        }
        
        # Normalize participant emails
        participant_emails = [email.lower() for email in participant_emails]
        
        # Track results
        present_count = 0
        missed_count = 0
        absent_students = []
        
        for email, enrollment_id in student_emails.items():
            if email in participant_emails:
                # Mark present
                self.mark_present(enrollment_id, session_id)
                present_count += 1
            else:
                # Mark missed
                self.mark_missed(enrollment_id, session_id)
                missed_count += 1
                absent_students.append(email)
        
        # Update session status to completed if not already
        if session.status != SessionStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED
            self.db.commit()
        
        return {
            "session_id": session_id,
            "total_enrolled": len(student_emails),
            "present_count": present_count,
            "missed_count": missed_count,
            "absent_students": absent_students,
        }
    
    # ============================================================
    # BULK OPERATIONS
    # ============================================================
    
    def bulk_mark_attendance(
        self, 
        session_id: int, 
        present_student_ids: List[int],
        excused_student_ids: List[int] = None,
        remarks: Optional[str] = None
    ) -> Dict[str, int]:
        """Mark attendance for multiple students."""
        if excused_student_ids is None:
            excused_student_ids = []
        
        # Get all active enrollments for this course
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.course_id == session.course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).all()
        
        present_count = 0
        excused_count = 0
        missed_count = 0
        
        for enrollment in enrollments:
            student_id = enrollment.student_id
            
            if student_id in present_student_ids:
                self.mark_present(enrollment.id, session_id, remarks=remarks)
                present_count += 1
            elif student_id in excused_student_ids:
                self.mark_excused(enrollment.id, session_id, remarks=remarks)
                excused_count += 1
            else:
                self.mark_missed(enrollment.id, session_id, remarks=remarks)
                missed_count += 1
        
        # Update session status
        if session.status != SessionStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED
            self.db.commit()
        
        return {
            "session_id": session_id,
            "present": present_count,
            "excused": excused_count,
            "missed": missed_count,
            "total": present_count + excused_count + missed_count,
        }
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_attendance_stats(self, enrollment_id: int) -> Dict[str, Any]:
        """Get attendance statistics for a student."""
        attendance_records = self.get_by_enrollment(enrollment_id)
        
        total = len(attendance_records)
        present = sum(1 for a in attendance_records if a.status == AttendanceStatus.PRESENT)
        missed = sum(1 for a in attendance_records if a.status == AttendanceStatus.MISSED)
        made_up = sum(1 for a in attendance_records if a.status == AttendanceStatus.MADE_UP)
        excused = sum(1 for a in attendance_records if a.status == AttendanceStatus.EXCUSED)
        
        attendance_percentage = (present + made_up) / total * 100 if total > 0 else 0
        
        return {
            "total": total,
            "present": present,
            "missed": missed,
            "made_up": made_up,
            "excused": excused,
            "attendance_percentage": round(attendance_percentage, 2),
        }
    
    def get_student_attendance_summary(self, student_id: int) -> Dict[str, Any]:
        """Get attendance summary for a student across all courses."""
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).all()
        
        total_present = 0
        total_missed = 0
        total_made_up = 0
        total_excused = 0
        course_summaries = []
        
        for enrollment in enrollments:
            stats = self.get_attendance_stats(enrollment.id)
            course = enrollment.course
            
            course_summaries.append({
                "course_id": course.id,
                "course_title": course.title,
                "attendance_percentage": stats["attendance_percentage"],
                "present": stats["present"],
                "missed": stats["missed"],
                "made_up": stats["made_up"],
                "excused": stats["excused"],
                "total": stats["total"],
            })
            
            total_present += stats["present"]
            total_missed += stats["missed"]
            total_made_up += stats["made_up"]
            total_excused += stats["excused"]
        
        total_sessions = total_present + total_missed + total_made_up + total_excused
        
        return {
            "total_present": total_present,
            "total_missed": total_missed,
            "total_made_up": total_made_up,
            "total_excused": total_excused,
            "total_sessions": total_sessions,
            "overall_attendance": round((total_present + total_made_up) / total_sessions * 100, 2) if total_sessions > 0 else 0,
            "course_summaries": course_summaries,
        }
    
    def get_session_attendance_summary(self, session_id: int) -> Dict[str, Any]:
        """Get attendance summary for a session (teacher view)."""
        attendance_records = self.get_by_session(session_id)
        session = self.db.query(Session).filter(Session.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        total_students = len(attendance_records)
        present = sum(1 for a in attendance_records if a.status == AttendanceStatus.PRESENT)
        missed = sum(1 for a in attendance_records if a.status == AttendanceStatus.MISSED)
        made_up = sum(1 for a in attendance_records if a.status == AttendanceStatus.MADE_UP)
        excused = sum(1 for a in attendance_records if a.status == AttendanceStatus.EXCUSED)
        
        # Get list of absent students
        absent_students = []
        for a in attendance_records:
            if a.status == AttendanceStatus.MISSED:
                absent_students.append({
                    "student_id": a.enrollment.student_id,
                    "student_name": a.enrollment.student.full_name,
                    "student_email": a.enrollment.student.email,
                })
        
        return {
            "session_id": session_id,
            "session_title": session.title,
            "course_id": session.course_id,
            "course_title": session.course.title if session.course else None,
            "total_students": total_students,
            "present": present,
            "missed": missed,
            "made_up": made_up,
            "excused": excused,
            "attendance_rate": round((present + made_up) / total_students * 100, 2) if total_students > 0 else 0,
            "absent_students": absent_students,
        }