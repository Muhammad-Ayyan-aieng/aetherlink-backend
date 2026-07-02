# ============================================================
# AETHER LINK - ENROLLMENT SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..repositories.enrollment_repository import EnrollmentRepository
from ..repositories.course_repository import CourseRepository
from ..repositories.user_repository import UserRepository
from ..repositories.payment_repository import PaymentRepository
from ..repositories.attendance_repository import AttendanceRepository
from ..repositories.session_repository import SessionRepository
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.user import UserRole
from ..models.course import CourseStatus
from ..schemas.enrollment import EnrollmentCreate, ProgressUpdate


class EnrollmentService:
    """Service for enrollment business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.enrollment_repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.session_repo = SessionRepository(db)
    
    # ============================================================
    # ENROLL
    # ============================================================
    
    def enroll_student(self, student_id: int, course_id: int) -> Enrollment:
        """
        Enroll a student in a course.
        
        Args:
            student_id: Student ID
            course_id: Course ID
            
        Returns:
            Created enrollment
            
        Raises:
            ValueError: If validation fails
        """
        # Check if student exists and is active
        student = self.user_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        if student.role != UserRole.STUDENT:
            raise ValueError("User is not a student")
        
        if not student.is_active:
            raise ValueError("Student account is inactive")
        
        # Check if course exists and is published
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.status != CourseStatus.PUBLISHED:
            raise ValueError("Course is not available for enrollment")
        
        # Check if already enrolled
        existing = self.enrollment_repo.get_by_student_and_course(student_id, course_id)
        if existing:
            if existing.status == EnrollmentStatus.ACTIVE:
                raise ValueError("Already enrolled in this course")
            elif existing.status == EnrollmentStatus.PENDING:
                raise ValueError("Enrollment already pending. Please complete payment.")
            elif existing.status == EnrollmentStatus.PAYMENT_VERIFICATION:
                raise ValueError("Enrollment is awaiting payment verification")
            elif existing.status == EnrollmentStatus.COMPLETED:
                raise ValueError("Already completed this course")
            elif existing.status == EnrollmentStatus.EXPIRED:
                raise ValueError("Previous enrollment expired. Please re-enroll.")
        
        # Create enrollment
        enrollment = self.enrollment_repo.create(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.PENDING,
            payment_amount=course.price,
            payment_method="easypaisa",
            payment_verified=False,
            progress_percentage=0,
        )
        
        # Create payment record
        self.payment_repo.create(
            enrollment_id=enrollment.id,
            student_id=student_id,
            amount=course.price,
            method="easypaisa",
            status="pending",
        )
        
        return enrollment
    
    # ============================================================
    # READ
    # ============================================================
    
    def get_enrollment(self, enrollment_id: int) -> Enrollment:
        """
        Get enrollment by ID.
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Enrollment
            
        Raises:
            ValueError: If enrollment not found
        """
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        return enrollment
    
    def get_enrollment_with_details(self, enrollment_id: int) -> Enrollment:
        """
        Get enrollment with all details.
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Enrollment with relationships
            
        Raises:
            ValueError: If enrollment not found
        """
        enrollment = self.enrollment_repo.get_full_details(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        return enrollment
    
    def get_student_enrollments(
        self, 
        student_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get enrollments for a student with filters.
        
        Args:
            student_id: Student ID
            status: Filter by status
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Enrollments and total count
        """
        if limit > 100:
            limit = 100
        
        # Get student
        student = self.user_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")
        
        if status:
            enrollments = self.enrollment_repo.get_by_status(EnrollmentStatus(status))
            enrollments = [e for e in enrollments if e.student_id == student_id]
            total = len(enrollments)
            enrollments = enrollments[skip:skip + limit]
        else:
            enrollments, total = self.enrollment_repo.get_by_student_paginated(student_id, skip, limit)
        
        return {
            "enrollments": enrollments,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    def get_course_enrollments(
        self, 
        course_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get enrollments for a course (teacher/admin only).
        
        Args:
            course_id: Course ID
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Enrollments and total count
        """
        if limit > 100:
            limit = 100
        
        enrollments, total = self.enrollment_repo.get_by_course_paginated(course_id, skip, limit)
        
        return {
            "enrollments": enrollments,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    # ============================================================
    # PAYMENT VERIFICATION (Admin)
    # ============================================================
    
    def verify_payment(self, enrollment_id: int, verified_by: int, notes: Optional[str] = None) -> Enrollment:
        """
        Verify payment for an enrollment (admin only).
        
        Args:
            enrollment_id: Enrollment ID
            verified_by: Admin ID
            notes: Verification notes
            
        Returns:
            Updated enrollment
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(verified_by)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        enrollment = self.enrollment_repo.get_by_id_or_fail(enrollment_id)
        
        if enrollment.status != EnrollmentStatus.PAYMENT_VERIFICATION:
            raise ValueError("Enrollment is not pending payment verification")
        
        if enrollment.payment_verified:
            raise ValueError("Payment already verified")
        
        # Verify payment
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.payment_verified = True
        enrollment.payment_verified_by = verified_by
        enrollment.payment_verified_at = datetime.utcnow()
        enrollment.expires_at = datetime.utcnow() + timedelta(days=90)
        
        if notes:
            enrollment.notes = notes
        
        # Update payment record
        payment = self.payment_repo.get_by_enrollment(enrollment_id)
        if payment:
            payment.status = "verified"
            payment.verified_by = verified_by
            payment.verified_at = datetime.utcnow()
            if notes:
                payment.verification_notes = notes
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def reject_payment(self, enrollment_id: int, verified_by: int, reason: str) -> Enrollment:
        """
        Reject payment for an enrollment (admin only).
        
        Args:
            enrollment_id: Enrollment ID
            verified_by: Admin ID
            reason: Rejection reason
            
        Returns:
            Updated enrollment
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(verified_by)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        enrollment = self.enrollment_repo.get_by_id_or_fail(enrollment_id)
        
        if enrollment.status != EnrollmentStatus.PAYMENT_VERIFICATION:
            raise ValueError("Enrollment is not pending payment verification")
        
        # Reject payment
        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.notes = f"Rejected: {reason}"
        
        # Update payment record
        payment = self.payment_repo.get_by_enrollment(enrollment_id)
        if payment:
            payment.status = "rejected"
            payment.verified_by = verified_by
            payment.rejected_at = datetime.utcnow()
            payment.rejection_reason = reason
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    # ============================================================
    # PROGRESS MANAGEMENT
    # ============================================================
    
    def update_progress(self, enrollment_id: int, progress: int) -> Enrollment:
        """
        Update student progress.
        
        Args:
            enrollment_id: Enrollment ID
            progress: Progress percentage (0-100)
            
        Returns:
            Updated enrollment
            
        Raises:
            ValueError: If validation fails
        """
        enrollment = self.enrollment_repo.get_by_id_or_fail(enrollment_id)
        
        if enrollment.status not in [EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED]:
            raise ValueError("Cannot update progress for inactive enrollment")
        
        if progress < 0 or progress > 100:
            raise ValueError("Progress must be between 0 and 100")
        
        enrollment.progress_percentage = progress
        
        # Auto-complete if progress is 100%
        if progress >= 100 and enrollment.status == EnrollmentStatus.ACTIVE:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def complete_enrollment(self, enrollment_id: int) -> Enrollment:
        """
        Manually mark enrollment as completed.
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Updated enrollment
            
        Raises:
            ValueError: If validation fails
        """
        enrollment = self.enrollment_repo.get_by_id_or_fail(enrollment_id)
        
        if enrollment.status == EnrollmentStatus.COMPLETED:
            raise ValueError("Enrollment already completed")
        
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = datetime.utcnow()
        enrollment.progress_percentage = 100
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def cancel_enrollment(self, enrollment_id: int) -> Enrollment:
        """
        Cancel enrollment (admin or student).
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Updated enrollment
            
        Raises:
            ValueError: If validation fails
        """
        enrollment = self.enrollment_repo.get_by_id_or_fail(enrollment_id)
        
        if enrollment.status in [EnrollmentStatus.COMPLETED, EnrollmentStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel enrollment with status {enrollment.status}")
        
        enrollment.status = EnrollmentStatus.CANCELLED
        
        # Update payment if exists
        payment = self.payment_repo.get_by_enrollment(enrollment_id)
        if payment and payment.status == "verified":
            payment.status = "refunded"
            payment.refunded_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    # ============================================================
    # ⭐ STUDENT DASHBOARD
    # ============================================================
    
    def get_student_dashboard(self, student_id: int) -> Dict[str, Any]:
        """
        Get complete dashboard data for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            Dashboard data
        """
        return self.enrollment_repo.get_student_dashboard(student_id)
    
    # ============================================================
    # TEACHER COURSE ATTENDANCE
    # ============================================================
    
    def get_teacher_course_attendance(self, course_id: int, teacher_id: int) -> List[Dict[str, Any]]:
        """
        Get attendance summary for a course (teacher view).
        
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
        
        return self.enrollment_repo.get_course_attendance_summary(course_id)
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    def check_enrollment_status(self, student_id: int, course_id: int) -> Dict[str, Any]:
        """
        Check enrollment status for a student and course.
        
        Args:
            student_id: Student ID
            course_id: Course ID
            
        Returns:
            Enrollment status
        """
        enrollment = self.enrollment_repo.get_by_student_and_course(student_id, course_id)
        
        if not enrollment:
            return {
                "enrolled": False,
                "status": None,
                "can_enroll": True,
            }
        
        return {
            "enrolled": True,
            "status": enrollment.status.value,
            "can_enroll": enrollment.status in [EnrollmentStatus.EXPIRED, EnrollmentStatus.CANCELLED],
            "enrollment_id": enrollment.id,
            "progress": enrollment.progress_percentage,
        }
    
    def is_enrolled(self, student_id: int, course_id: int) -> bool:
        """
        Check if a student is actively enrolled in a course.
        
        Args:
            student_id: Student ID
            course_id: Course ID
            
        Returns:
            True if actively enrolled
        """
        return self.enrollment_repo.is_active_enrolled(student_id, course_id)
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_enrollment_stats(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Get enrollment statistics (admin only).
        
        Args:
            admin_user_id: Admin user ID
            
        Returns:
            Enrollment statistics
        """
        admin = self.user_repo.get_by_id(admin_user_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.enrollment_repo.get_stats()