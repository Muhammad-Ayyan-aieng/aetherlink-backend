# ============================================================
# AETHER LINK - ENROLLMENTS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any
import logging

from ...core.database import get_db
from ...core.dependencies import (
    get_current_user,
    get_current_teacher_user,
    get_current_admin_user,
    rate_limiter,
)
from ...services.enrollment_service import EnrollmentService
from ...services.course_service import CourseService
from ...services.attendance_service import AttendanceService
from ...services.session_service import SessionService
from ...schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    PaymentVerification,
    ProgressUpdate,
    StudentEnrollmentResponse,
    EnrollmentDetailResponse,
)
from ...models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# ============================================================
# STUDENT: ENROLL
# ============================================================

@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter)],
    summary="Enroll in a course",
    description="Enroll the current student in a course.",
)
def enroll_student(
    enrollment_data: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Enroll the current student in a course.
    
    - **course_id**: Course ID
    """
    try:
        enrollment_service = EnrollmentService(db)
        
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can enroll in courses",
            )
        
        result = enrollment_service.enroll_student(
            student_id=current_user.id,
            course_id=enrollment_data.course_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Enroll error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enrolling: {str(e)}",
        )


# ============================================================
# STUDENT: MY ENROLLMENTS (FIXED)
# ============================================================

@router.get(
    "/me",
    dependencies=[Depends(rate_limiter)],
    summary="Get my enrollments",
    description="Get all enrollments for the current student.",
)
def get_my_enrollments(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all enrollments for the current student.
    
    - **status**: Filter by enrollment status
    - **skip**: Pagination offset
    - **limit**: Max results (1-100)
    """
    try:
        # FIX: Check if user is a student FIRST
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their enrollments",
            )
        
        enrollment_service = EnrollmentService(db)
        result = enrollment_service.get_student_enrollments(
            student_id=current_user.id,
            status=status,
            skip=skip,
            limit=limit,
        )
        
        # Convert to response format
        enrollments = []
        for enrollment in result.get("enrollments", []):
            # Calculate session stats
            total_sessions = 0
            completed_sessions = 0
            missed_sessions = 0
            next_session_date = None
            next_session_title = None
            
            if enrollment.course:
                total_sessions = enrollment.course.total_sessions or 0
                
                # Get attendance for this enrollment
                try:
                    attendance_service = AttendanceService(db)
                    attendance_stats = attendance_service.get_student_attendance_stats(
                        student_id=current_user.id,
                        course_id=enrollment.course_id
                    )
                    completed_sessions = attendance_stats.get("present", 0) + attendance_stats.get("made_up", 0)
                    missed_sessions = attendance_stats.get("missed", 0)
                except Exception as e:
                    logger.warning(f"Error getting attendance stats: {e}")
                    completed_sessions = 0
                    missed_sessions = 0
                
                # Get next session
                try:
                    session_service = SessionService(db)
                    next_session = session_service.get_next_session_for_course(enrollment.course_id)
                    if next_session:
                        next_session_date = next_session.date_time
                        next_session_title = next_session.title
                except Exception as e:
                    logger.warning(f"Error getting next session: {e}")
                    next_session_date = None
                    next_session_title = None
            
            enrollments.append({
                "id": enrollment.id,
                "course_id": enrollment.course_id,
                "course_title": enrollment.course.title if enrollment.course else None,
                "course_slug": enrollment.course.slug if enrollment.course else None,
                "course_thumbnail": enrollment.course.thumbnail if enrollment.course else None,
                "teacher_name": enrollment.course.teacher.full_name if enrollment.course and enrollment.course.teacher else None,
                "status": enrollment.status.value if enrollment.status else None,
                "progress_percentage": enrollment.progress_percentage or 0,
                "enrolled_at": enrollment.enrolled_at,
                "expires_at": enrollment.expires_at,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "missed_sessions": missed_sessions,
                "next_session_date": next_session_date,
                "next_session_title": next_session_title,
            })
        
        return enrollments
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get my enrollments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching enrollments: {str(e)}",
        )


# ============================================================
# STUDENT: DASHBOARD ⭐
# ============================================================

@router.get(
    "/dashboard",
    dependencies=[Depends(rate_limiter)],
    summary="Get student dashboard",
    description="Get complete dashboard data for the student.",
)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get complete dashboard data for the current student.
    
    Includes:
    - Enrolled courses with progress
    - Next session details
    - Missed sessions count
    - Average progress
    """
    try:
        enrollment_service = EnrollmentService(db)
        
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their dashboard",
            )
        
        dashboard = enrollment_service.get_student_dashboard(current_user.id)
        return dashboard
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard: {str(e)}",
        )


# ============================================================
# GET ENROLLMENT (Student/Teacher/Admin)
# ============================================================

@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentDetailResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get enrollment details",
    description="Get enrollment details (student/teacher/admin).",
)
def get_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get enrollment details.
    
    - **enrollment_id**: Enrollment ID
    """
    try:
        enrollment_service = EnrollmentService(db)
        enrollment = enrollment_service.get_enrollment_with_details(enrollment_id)
        
        # Check permission
        if (
            enrollment.student_id != current_user.id
            and enrollment.course.teacher_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this enrollment",
            )
        
        return enrollment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Get enrollment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching enrollment: {str(e)}",
        )


# ============================================================
# ADMIN: PAYMENT VERIFICATION
# ============================================================

@router.post(
    "/{enrollment_id}/verify-payment",
    response_model=EnrollmentResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Verify payment (admin only)",
    description="Verify payment and activate enrollment.",
)
def verify_payment(
    enrollment_id: int,
    verification_data: PaymentVerification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Verify payment and activate enrollment.
    
    **Admin only.**
    
    - **enrollment_id**: Enrollment ID
    - **notes**: Optional verification notes
    """
    try:
        enrollment_service = EnrollmentService(db)
        enrollment = enrollment_service.verify_payment(
            enrollment_id=enrollment_id,
            verified_by=current_user.id,
            notes=verification_data.notes,
        )
        return enrollment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Verify payment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying payment: {str(e)}",
        )


@router.post(
    "/{enrollment_id}/reject-payment",
    response_model=EnrollmentResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Reject payment (admin only)",
    description="Reject payment and cancel enrollment.",
)
def reject_payment(
    enrollment_id: int,
    verification_data: PaymentVerification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Reject payment and cancel enrollment.
    
    **Admin only.**
    
    - **enrollment_id**: Enrollment ID
    - **notes**: Rejection reason
    """
    try:
        enrollment_service = EnrollmentService(db)
        
        if not verification_data.notes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason required",
            )
        
        enrollment = enrollment_service.reject_payment(
            enrollment_id=enrollment_id,
            verified_by=current_user.id,
            reason=verification_data.notes,
        )
        return enrollment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Reject payment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting payment: {str(e)}",
        )


# ============================================================
# PROGRESS UPDATE (Student)
# ============================================================

@router.put(
    "/{enrollment_id}/progress",
    response_model=EnrollmentResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Update progress",
    description="Update student progress.",
)
def update_progress(
    enrollment_id: int,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update student progress.
    
    - **enrollment_id**: Enrollment ID
    - **progress_percentage**: 0-100
    """
    try:
        enrollment_service = EnrollmentService(db)
        
        # Check if student owns this enrollment
        enrollment = enrollment_service.get_enrollment(enrollment_id)
        if enrollment.student_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this enrollment",
            )
        
        enrollment = enrollment_service.update_progress(
            enrollment_id=enrollment_id,
            progress=progress_data.progress_percentage,
        )
        return enrollment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Update progress error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating progress: {str(e)}",
        )


# ============================================================
# COMPLETE ENROLLMENT
# ============================================================

@router.post(
    "/{enrollment_id}/complete",
    response_model=EnrollmentResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Complete enrollment",
    description="Mark enrollment as completed.",
)
def complete_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Mark enrollment as completed.
    
    - **enrollment_id**: Enrollment ID
    """
    try:
        enrollment_service = EnrollmentService(db)
        
        # Check permission
        enrollment = enrollment_service.get_enrollment(enrollment_id)
        if (
            enrollment.student_id != current_user.id
            and enrollment.course.teacher_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to complete this enrollment",
            )
        
        enrollment = enrollment_service.complete_enrollment(enrollment_id)
        return enrollment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Complete enrollment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing enrollment: {str(e)}",
        )


# ============================================================
# CANCEL ENROLLMENT (Student/Admin)
# ============================================================

@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limiter)],
    summary="Cancel enrollment",
    description="Cancel enrollment (student or admin).",
)
def cancel_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Cancel enrollment.
    
    - **enrollment_id**: Enrollment ID
    """
    try:
        enrollment_service = EnrollmentService(db)
        
        # Check permission
        enrollment = enrollment_service.get_enrollment(enrollment_id)
        if (
            enrollment.student_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this enrollment",
            )
        
        enrollment_service.cancel_enrollment(enrollment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Cancel enrollment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling enrollment: {str(e)}",
        )


# ============================================================
# TEACHER: COURSE ENROLLMENTS
# ============================================================

@router.get(
    "/course/{course_id}",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get course enrollments",
    description="Get all enrollments for a course (teacher/admin).",
)
def get_course_enrollments(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all enrollments for a course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    """
    try:
        enrollment_service = EnrollmentService(db)
        course_service = CourseService(db)
        
        # Check if teacher owns this course
        course = course_service.get_course(course_id)
        if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this course's enrollments",
            )
        
        result = enrollment_service.get_course_enrollments(
            course_id=course_id,
            teacher_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Get course enrollments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching course enrollments: {str(e)}",
        )