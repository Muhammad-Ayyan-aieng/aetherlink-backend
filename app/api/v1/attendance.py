# ============================================================
# AETHER LINK - ATTENDANCE API ⭐ CRITICAL
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
from ...services.attendance_service import AttendanceService
from ...services.enrollment_service import EnrollmentService
from ...schemas.attendance import (
    AttendanceMark,
    AttendanceUpdate,
    WatchRecording,
    BulkAttendanceMark,
    AttendanceResponse,
    MissedSessionResponse,
    AttendanceSummary,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/attendance", tags=["Attendance"])


# ============================================================
# STUDENT: GET MISSED SESSIONS ⭐
# ============================================================

@router.get(
    "/missed",
    response_model=List[MissedSessionResponse],
    dependencies=[Depends(rate_limiter)],
    summary="Get missed sessions",
    description="Get all missed sessions for the current student.",
)
def get_missed_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all missed sessions for the current student.
    
    **Student only.**
    
    Powers the 'Missed Sessions' widget on the dashboard.
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view missed sessions",
            )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.get_missed_sessions(current_user.id)
        
        # If no missed sessions, return empty list
        if not result or result.get("missed_count", 0) == 0:
            return []
        
        return result.get("missed_sessions", [])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: GET ATTENDANCE SUMMARY
# ============================================================

@router.get(
    "/summary",
    response_model=AttendanceSummary,
    dependencies=[Depends(rate_limiter)],
    summary="Get attendance summary",
    description="Get attendance summary for the current student.",
)
def get_attendance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get attendance summary for the current student.
    
    **Student only.**
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their attendance summary",
            )
        
        attendance_service = AttendanceService(db)
        summary = attendance_service.get_student_attendance_summary(current_user.id)
        
        # If no attendance records, return empty summary
        if not summary or summary.get("total_sessions", 0) == 0:
            return {
                "student_id": current_user.id,
                "course_id": None,
                "total_sessions": 0,
                "present": 0,
                "absent": 0,
                "missed": 0,
                "made_up": 0,
                "attendance_rate": 0,
                "missed_count": 0,
                "missed_can_be_made_up": False,
                "message": "No attendance records found"
            }
        
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: GET MY ATTENDANCE (Paginated)
# ============================================================

@router.get(
    "/my",
    dependencies=[Depends(rate_limiter)],
    summary="Get my attendance",
    description="Get all attendance records for the current student.",
)
def get_my_attendance(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all attendance records for the current student.
    
    **Student only.**
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their attendance",
            )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.get_student_attendance(
            student_id=current_user.id,
            requesting_user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        
        # If no attendance records, return empty result
        if not result or result.get("total", 0) == 0:
            return {
                "student_id": current_user.id,
                "student_name": current_user.full_name,
                "attendance": [],
                "total": 0,
                "summary": {
                    "present": 0,
                    "absent": 0,
                    "missed": 0,
                    "made_up": 0,
                    "attendance_rate": 0,
                    "total_sessions": 0
                },
                "pagination": {
                    "page": 1,
                    "page_size": limit,
                    "total_pages": 0
                },
                "message": "No attendance records found"
            }
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: MARK AS MADE UP (80% Rule)
# ============================================================

@router.post(
    "/made-up",
    response_model=AttendanceResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Mark as made up",
    description="Mark a missed session as made up after watching recording (>=80%).",
)
def mark_made_up(
    watch_data: WatchRecording,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Mark a missed session as made up.
    
    **Student only.**
    
    - **attendance_id**: Attendance record ID
    - **watch_percentage**: 0-100 (must be >= 80%)
    - **watch_time_minutes**: Minutes watched (optional)
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can mark sessions as made up",
            )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.mark_made_up(
            student_id=current_user.id,
            watch_data=watch_data,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER: MARK ATTENDANCE (Single)
# ============================================================

@router.post(
    "/mark",
    response_model=AttendanceResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Mark attendance",
    description="Mark attendance for a single student (teacher or admin).",
)
def mark_attendance(
    mark_data: AttendanceMark,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Mark attendance for a single student.
    
    **Teacher or Admin only.**
    
    - **student_id**: Student ID
    - **session_id**: Session ID
    - **status**: present, absent, missed
    """
    try:
        attendance_service = AttendanceService(db)
        result = attendance_service.mark_attendance(
            teacher_id=current_user.id,
            mark_data=mark_data,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER: BULK MARK ATTENDANCE
# ============================================================

@router.post(
    "/bulk",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Bulk mark attendance",
    description="Mark attendance for multiple students (teacher or admin).",
)
def bulk_mark_attendance(
    bulk_data: BulkAttendanceMark,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Bulk mark attendance for multiple students.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    - **attendance_list**: List of {student_id, status}
    """
    try:
        attendance_service = AttendanceService(db)
        result = attendance_service.bulk_mark_attendance(
            teacher_id=current_user.id,
            bulk_data=bulk_data,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER: GET SESSION ATTENDANCE
# ============================================================

@router.get(
    "/session/{session_id}",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get session attendance",
    description="Get all attendance records for a session.",
)
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all attendance records for a session.
    
    **Teacher or Admin only.**
    """
    try:
        attendance_service = AttendanceService(db)
        result = attendance_service.get_session_attendance(
            session_id=session_id,
            teacher_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER: GET COURSE ATTENDANCE SUMMARY
# ============================================================

@router.get(
    "/course/{course_id}",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get course attendance summary",
    description="Get attendance summary for an entire course.",
)
def get_course_attendance(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get attendance summary for an entire course.
    
    **Teacher or Admin only.**
    """
    try:
        attendance_service = AttendanceService(db)
        result = attendance_service.get_course_attendance_summary(
            course_id=course_id,
            teacher_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: GET STUDENT ATTENDANCE
# ============================================================

@router.get(
    "/student/{student_id}",
    dependencies=[Depends(rate_limiter)],
    summary="Get student attendance",
    description="Get attendance records for a specific student.",
)
def get_student_attendance(
    student_id: int,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get attendance records for a specific student.
    
    **Student can view own. Teacher/Admin can view any.**
    """
    try:
        # Check permission
        if student_id != current_user.id:
            if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this student's attendance",
                )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.get_student_attendance(
            student_id=student_id,
            requesting_user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        
        # If no attendance records, return empty result
        if not result or result.get("total", 0) == 0:
            student = db.query(User).filter(User.id == student_id).first()
            return {
                "student_id": student_id,
                "student_name": student.full_name if student else "Unknown",
                "attendance": [],
                "total": 0,
                "summary": {
                    "present": 0,
                    "absent": 0,
                    "missed": 0,
                    "made_up": 0,
                    "attendance_rate": 0,
                    "total_sessions": 0
                },
                "pagination": {
                    "page": 1,
                    "page_size": limit,
                    "total_pages": 0
                },
                "message": "No attendance records found"
            }
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# AUTO ATTENDANCE (Zoom/BBB Webhook)
# ============================================================

@router.post(
    "/auto",
    dependencies=[Depends(rate_limiter)],
    summary="Auto-mark attendance",
    description="Auto-mark attendance from Zoom/BBB webhook.",
)
async def auto_mark_attendance(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Auto-mark attendance from Zoom/BBB webhook.
    
    **Public endpoint but should be secured with API key.**
    
    Expected payload:
    {
        "session_id": 123,
        "participants": [
            {
                "student_id": 1,
                "email": "student@example.com",
                "join_time": "2024-01-01T10:00:00Z",
                "leave_time": "2024-01-01T11:00:00Z",
                "duration_minutes": 60
            }
        ]
    }
    """
    try:
        data = await request.json()
        
        session_id = data.get("session_id")
        participants = data.get("participants", [])
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id required",
            )
        
        if not participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="participants required",
            )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.auto_mark_attendance(
            session_id=session_id,
            participant_data=participants,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process auto-attendance: {str(e)}",
        )


# ============================================================
# ADMIN: OVERALL ATTENDANCE STATS
# ============================================================

@router.get(
    "/stats/overall",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get overall attendance stats",
    description="Get overall attendance statistics (admin only).",
)
def get_overall_attendance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get overall attendance statistics for the entire platform.
    
    **Admin only.**
    """
    try:
        attendance_service = AttendanceService(db)
        
        # Get all courses
        course_service = EnrollmentService(db)
        courses = course_service.course_repo.get_all()
        
        total_sessions = 0
        total_students = 0
        total_present = 0
        total_missed = 0
        total_made_up = 0
        
        for course in courses[0]:  # courses is a tuple
            if course.id:
                try:
                    stats = attendance_service.get_course_attendance_summary(course.id, 0)
                    # Skip if no students
                    if stats.get("total_students", 0) > 0:
                        total_students += stats.get("total_students", 0)
                        total_sessions += stats.get("total_sessions", 0)
                        for student in stats.get("students", []):
                            total_present += student.get("present", 0)
                            total_missed += student.get("missed", 0)
                            total_made_up += student.get("made_up", 0)
                except:
                    pass
        
        return {
            "total_sessions": total_sessions,
            "total_students": total_students,
            "total_present": total_present,
            "total_missed": total_missed,
            "total_made_up": total_made_up,
            "overall_attendance_rate": round(
                (total_present + total_made_up) / (total_present + total_missed + total_made_up) * 100, 2
            ) if (total_present + total_missed + total_made_up) > 0 else 0
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )