# ============================================================
# AETHER LINK - ENROLLMENT REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.user import User
from ..models.course import Course
from ..models.payments import Payment
from ..models.attendance import Attendance, AttendanceStatus
from ..models.sessions import Session , SessionStatus


class EnrollmentRepository(BaseRepository[Enrollment]):
    """Repository for Enrollment model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Enrollment)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_student(self, student_id: int) -> List[Enrollment]:
        """Get all enrollments for a student."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    def get_by_student_paginated(
        self, 
        student_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Enrollment], int]:
        """Get paginated enrollments for a student."""
        query = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.deleted_at.is_(None)
        )
        total = query.count()
        enrollments = query.offset(skip).limit(limit).all()
        return enrollments, total
    
    def get_by_course(self, course_id: int) -> List[Enrollment]:
        """Get all enrollments for a course."""
        return self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    def get_by_course_paginated(
        self, 
        course_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Enrollment], int]:
        """Get paginated enrollments for a course."""
        query = self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.deleted_at.is_(None)
        )
        total = query.count()
        enrollments = query.offset(skip).limit(limit).all()
        return enrollments, total
    
    def get_by_student_and_course(
        self, 
        student_id: int, 
        course_id: int
    ) -> Optional[Enrollment]:
        """Get specific enrollment by student and course."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # STATUS-BASED QUERIES
    # ============================================================
    
    def get_active_by_student(self, student_id: int) -> List[Enrollment]:
        """Get active enrollments for a student."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    def get_active_by_course(self, course_id: int) -> List[Enrollment]:
        """Get active enrollments for a course."""
        return self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    def get_pending_payments(self) -> List[Enrollment]:
        """Get enrollments with pending payments."""
        return self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.PAYMENT_VERIFICATION,
            Enrollment.payment_verified == False,
            Enrollment.deleted_at.is_(None)
        ).order_by(Enrollment.created_at).all()
    
    def get_by_status(self, status: EnrollmentStatus) -> List[Enrollment]:
        """Get enrollments by status."""
        return self.db.query(Enrollment).filter(
            Enrollment.status == status,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    def get_expired(self) -> List[Enrollment]:
        """Get expired enrollments."""
        now = datetime.utcnow()
        return self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.expires_at.is_not(None),
            Enrollment.expires_at < now,
            Enrollment.deleted_at.is_(None)
        ).all()
    
    # ============================================================
    # RELATIONSHIP QUERIES (Eager Loading)
    # ============================================================
    
    def get_with_payment(self, enrollment_id: int) -> Optional[Enrollment]:
        """Get enrollment with payment loaded."""
        return self.db.query(Enrollment).options(
            joinedload(Enrollment.payment)
        ).filter(
            Enrollment.id == enrollment_id,
            Enrollment.deleted_at.is_(None)
        ).first()
    
    def get_with_attendance(self, enrollment_id: int) -> Optional[Enrollment]:
        """Get enrollment with attendance records loaded."""
        return self.db.query(Enrollment).options(
            joinedload(Enrollment.attendance_records)
        ).filter(
            Enrollment.id == enrollment_id,
            Enrollment.deleted_at.is_(None)
        ).first()
    
    def get_with_student_and_course(self, enrollment_id: int) -> Optional[Enrollment]:
        """Get enrollment with student and course loaded."""
        return self.db.query(Enrollment).options(
            joinedload(Enrollment.student),
            joinedload(Enrollment.course)
        ).filter(
            Enrollment.id == enrollment_id,
            Enrollment.deleted_at.is_(None)
        ).first()
    
    def get_full_details(self, enrollment_id: int) -> Optional[Enrollment]:
        """Get enrollment with all relationships loaded."""
        return self.db.query(Enrollment).options(
            joinedload(Enrollment.student),
            joinedload(Enrollment.course),
            joinedload(Enrollment.payment),
            joinedload(Enrollment.attendance_records)
        ).filter(
            Enrollment.id == enrollment_id,
            Enrollment.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def verify_payment(self, enrollment_id: int, verified_by: int) -> Enrollment:
        """Verify payment and activate enrollment."""
        enrollment = self.get_by_id_or_fail(enrollment_id)
        
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.payment_verified = True
        enrollment.payment_verified_by = verified_by
        enrollment.payment_verified_at = datetime.utcnow()
        
        # Set expiry (90 days from now)
        enrollment.expires_at = datetime.utcnow() + timedelta(days=90)
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def reject_payment(self, enrollment_id: int, notes: Optional[str] = None) -> Enrollment:
        """Reject payment and cancel enrollment."""
        enrollment = self.get_by_id_or_fail(enrollment_id)
        
        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.notes = notes
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def activate_enrollment(self, enrollment_id: int) -> Enrollment:
        """Activate an enrollment."""
        enrollment = self.get_by_id_or_fail(enrollment_id)
        
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.expires_at = datetime.utcnow() + timedelta(days=90)
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def complete_enrollment(self, enrollment_id: int) -> Enrollment:
        """Mark enrollment as completed."""
        enrollment = self.get_by_id_or_fail(enrollment_id)
        
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = datetime.utcnow()
        enrollment.progress_percentage = 100
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def cancel_enrollment(self, enrollment_id: int) -> Enrollment:
        """Cancel an enrollment."""
        enrollment = self.get_by_id_or_fail(enrollment_id)
        
        enrollment.status = EnrollmentStatus.CANCELLED
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def update_progress(self, enrollment_id: int, progress: int) -> Enrollment:
        """Update student progress."""
        enrollment = self.get_by_id_or_fail(enrollment_id)
        
        if progress < 0:
            progress = 0
        elif progress > 100:
            progress = 100
        
        enrollment.progress_percentage = progress
        
        # Auto-complete if progress is 100%
        if progress >= 100 and enrollment.status == EnrollmentStatus.ACTIVE:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    # ============================================================
    # STUDENT DASHBOARD ⭐
    # ============================================================
    
    def get_student_dashboard(self, student_id: int) -> dict:
        """Get complete dashboard data for a student."""
        enrollments = self.get_active_by_student(student_id)
        
        dashboard_data = {
            "enrollments": [],
            "total_courses": len(enrollments),
            "average_progress": 0,
            "total_missed_sessions": 0,
        }
        
        total_progress = 0
        for enrollment in enrollments:
            # Count missed sessions for this enrollment
            missed_count = self.db.query(Attendance).filter(
                Attendance.enrollment_id == enrollment.id,
                Attendance.status == AttendanceStatus.MISSED
            ).count()
            
            # Get course details
            course = enrollment.course
            total_sessions = self.db.query(Session).filter(
                Session.course_id == course.id,
                Session.deleted_at.is_(None)
            ).count()
            
            # Get next session
            next_session = self.db.query(Session).filter(
                Session.course_id == course.id,
                Session.date_time > datetime.utcnow(),
                Session.status == SessionStatus.UPCOMING,
                Session.deleted_at.is_(None)
            ).order_by(Session.date_time).first()
            
            # Get completed sessions
            completed_sessions = self.db.query(Attendance).filter(
                Attendance.enrollment_id == enrollment.id,
                Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.MADE_UP])
            ).count()
            
            dashboard_data["enrollments"].append({
                "enrollment_id": enrollment.id,
                "course_id": course.id,
                "course_title": course.title,
                "course_slug": course.slug,
                "course_thumbnail": course.thumbnail,
                "teacher_name": course.teacher.full_name if course.teacher else None,
                "progress": enrollment.progress_percentage,
                "status": enrollment.status,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "missed_sessions": missed_count,
                "next_session": {
                    "id": next_session.id if next_session else None,
                    "title": next_session.title if next_session else None,
                    "date_time": next_session.date_time if next_session else None,
                    "zoom_join_url": next_session.zoom_join_url if next_session else None,
                } if next_session else None,
                "enrolled_at": enrollment.enrolled_at,
                "expires_at": enrollment.expires_at,
            })
            
            total_progress += enrollment.progress_percentage
            dashboard_data["total_missed_sessions"] += missed_count
        
        if len(enrollments) > 0:
            dashboard_data["average_progress"] = total_progress // len(enrollments)
        
        return dashboard_data
    
    # ============================================================
    # ATTENDANCE SUMMARY (Teacher View)
    # ============================================================
    
    def get_course_attendance_summary(self, course_id: int) -> List[dict]:
        """Get attendance summary for all students in a course."""
        enrollments = self.get_active_by_course(course_id)
        summary = []
        
        total_sessions = self.db.query(Session).filter(
            Session.course_id == course_id,
            Session.deleted_at.is_(None)
        ).count()
        
        for enrollment in enrollments:
            student = enrollment.student
            
            # Count attendance records
            attended = self.db.query(Attendance).filter(
                Attendance.enrollment_id == enrollment.id,
                Attendance.status == AttendanceStatus.PRESENT
            ).count()
            
            missed = self.db.query(Attendance).filter(
                Attendance.enrollment_id == enrollment.id,
                Attendance.status == AttendanceStatus.MISSED
            ).count()
            
            made_up = self.db.query(Attendance).filter(
                Attendance.enrollment_id == enrollment.id,
                Attendance.status == AttendanceStatus.MADE_UP
            ).count()
            
            excused = self.db.query(Attendance).filter(
                Attendance.enrollment_id == enrollment.id,
                Attendance.status == AttendanceStatus.EXCUSED
            ).count()
            
            attendance_percentage = (attended + made_up) / total_sessions * 100 if total_sessions > 0 else 0
            
            summary.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "student_email": student.email,
                "total_sessions": total_sessions,
                "present": attended,
                "missed": missed,
                "made_up": made_up,
                "excused": excused,
                "attendance_percentage": round(attendance_percentage, 2),
                "last_attended": self.db.query(Attendance).filter(
                    Attendance.enrollment_id == enrollment.id,
                    Attendance.status == AttendanceStatus.PRESENT
                ).order_by(Attendance.created_at.desc()).first().created_at if attended > 0 else None,
            })
        
        return summary
    
    # ============================================================
    # VALIDATION OPERATIONS
    # ============================================================
    
    def is_enrolled(self, student_id: int, course_id: int) -> bool:
        """Check if a student is enrolled in a course."""
        enrollment = self.get_by_student_and_course(student_id, course_id)
        return enrollment is not None and enrollment.status == EnrollmentStatus.ACTIVE
    
    def is_active_enrolled(self, student_id: int, course_id: int) -> bool:
        """Check if a student has an active enrollment."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).first() is not None
    
    # ============================================================
    # COUNT OPERATIONS
    # ============================================================
    
    def count_by_student(self, student_id: int) -> int:
        """Count enrollments for a student."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.deleted_at.is_(None)
        ).count()
    
    def count_by_course_active(self, course_id: int) -> int:
        """Count active enrollments for a course."""
        return self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).count()
    
    def count_pending_verification(self) -> int:
        """Count enrollments pending payment verification."""
        return self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.PAYMENT_VERIFICATION,
            Enrollment.payment_verified == False,
            Enrollment.deleted_at.is_(None)
        ).count()
    
    def get_stats(self) -> dict:
        """Get enrollment statistics."""
        total = self.db.query(Enrollment).filter(Enrollment.deleted_at.is_(None)).count()
        active = self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.deleted_at.is_(None)
        ).count()
        completed = self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.COMPLETED,
            Enrollment.deleted_at.is_(None)
        ).count()
        pending = self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.PENDING,
            Enrollment.deleted_at.is_(None)
        ).count()
        payment_verification = self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.PAYMENT_VERIFICATION,
            Enrollment.deleted_at.is_(None)
        ).count()
        
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "pending": pending,
            "payment_verification": payment_verification,
        }