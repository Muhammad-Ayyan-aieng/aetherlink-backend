# ============================================================
# AETHER LINK - ENROLLMENTS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any

from ...core.database import get_db
from ...core.dependencies import (
    get_current_user,
    get_current_teacher_user,
    get_current_admin_user,
    rate_limiter,
)
from ...services.enrollment_service import EnrollmentService
from ...services.course_service import CourseService
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
        
        enrollment = enrollment_service.enroll_student(
            student_id=current_user.id,
            course_id=enrollment_data.course_id,
        )
        return enrollment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: MY ENROLLMENTS
# ============================================================

@router.get(
    "/me",
    response_model=List[StudentEnrollmentResponse],
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
        enrollment_service = EnrollmentService(db)
        
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their enrollments",
            )
        
        result = enrollment_service.get_student_enrollments(
            student_id=current_user.id,
            status=status,
            skip=skip,
            limit=limit,
        )
        
        return result["enrollments"]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
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


# ============================================================
# TEACHER: COURSE ATTENDANCE
# ============================================================

@router.get(
    "/course/{course_id}/attendance",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get course attendance",
    description="Get attendance summary for a course (teacher).",
)
def get_course_attendance(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get attendance summary for a course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    """
    try:
        enrollment_service = EnrollmentService(db)
        attendance = enrollment_service.get_teacher_course_attendance(
            course_id=course_id,
            teacher_id=current_user.id,
        )
        return {
            "course_id": course_id,
            "students": attendance,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )