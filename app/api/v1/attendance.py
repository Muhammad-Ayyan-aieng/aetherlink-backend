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
# STUDENT: MISSED SESSIONS ⭐
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
        missed_sessions = attendance_service.get_missed_sessions(current_user.id)
        return missed_sessions
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: WATCH RECORDING ⭐
# ============================================================

@router.post(
    "/watch",
    response_model=dict,
    dependencies=[Depends(rate_limiter)],
    summary="Watch recording",
    description="Student watches a recording (auto-made-up at 80%).",
)
def watch_recording(
    watch_data: WatchRecording,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Watch a recording and update progress.
    
    **Student only.**
    
    - **enrollment_id**: Enrollment ID
    - **session_id**: Session ID
    - **watched_percentage**: 0-100
    
    Auto-marks as MADE_UP when watched_percentage >= 80%.
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can watch recordings",
            )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.watch_recording(
            enrollment_id=watch_data.enrollment_id,
            session_id=watch_data.session_id,
            watched_percentage=watch_data.watched_percentage,
        )
        
        # Check if student owns this enrollment
        enrollment = attendance_service.enrollment_repo.get_by_id(watch_data.enrollment_id)
        if not enrollment or enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to watch this recording",
            )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: ATTENDANCE SUMMARY
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
        summary = attendance_service.get_attendance_summary(current_user.id)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: MARK ATTENDANCE
# ============================================================

@router.post(
    "/mark",
    response_model=AttendanceResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Mark attendance",
    description="Mark attendance for a student (teacher or admin).",
)
def mark_attendance(
    mark_data: AttendanceMark,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Mark attendance for a student.
    
    **Teacher or Admin only.**
    
    - **enrollment_id**: Enrollment ID
    - **session_id**: Session ID
    - **status**: present, missed, excused
    - **remarks**: Optional remarks
    """
    try:
        attendance_service = AttendanceService(db)
        
        # Map status to service method
        if mark_data.status.value == "present":
            result = attendance_service.mark_present(
                enrollment_id=mark_data.enrollment_id,
                session_id=mark_data.session_id,
                verified_by=current_user.id,
                remarks=mark_data.remarks,
            )
        elif mark_data.status.value == "missed":
            result = attendance_service.mark_missed(
                enrollment_id=mark_data.enrollment_id,
                session_id=mark_data.session_id,
                remarks=mark_data.remarks,
            )
        elif mark_data.status.value == "excused":
            result = attendance_service.mark_excused(
                enrollment_id=mark_data.enrollment_id,
                session_id=mark_data.session_id,
                verified_by=current_user.id,
                remarks=mark_data.remarks,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid attendance status",
            )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: SESSION ATTENDANCE
# ============================================================

@router.get(
    "/session/{session_id}",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get session attendance",
    description="Get attendance summary for a session (teacher or admin).",
)
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get attendance summary for a session.
    
    **Teacher or Admin only.**
    """
    try:
        attendance_service = AttendanceService(db)
        summary = attendance_service.get_session_attendance(
            session_id=session_id,
            teacher_id=current_user.id,
        )
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: BULK ATTENDANCE
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
    - **present_student_ids**: List of student IDs present
    - **excused_student_ids**: List of student IDs excused
    """
    try:
        attendance_service = AttendanceService(db)
        result = attendance_service.bulk_mark_attendance(
            session_id=bulk_data.session_id,
            present_student_ids=bulk_data.present_student_ids,
            excused_student_ids=bulk_data.excused_student_ids,
            teacher_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: ZOOM SYNC ⭐
# ============================================================

@router.post(
    "/sync-zoom",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Sync Zoom attendance",
    description="Sync attendance from Zoom participant list (teacher or admin).",
)
def sync_zoom_attendance(
    sync_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync attendance from Zoom participant list.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    - **participant_emails**: List of participant emails from Zoom
    """
    try:
        session_id = sync_data.get("session_id")
        participant_emails = sync_data.get("participant_emails", [])
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id required",
            )
        
        if not participant_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="participant_emails required",
            )
        
        attendance_service = AttendanceService(db)
        result = attendance_service.sync_zoom_attendance(
            session_id=session_id,
            participant_emails=participant_emails,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER: COURSE ATTENDANCE STATS
# ============================================================

@router.get(
    "/teacher/course/{course_id}",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get course attendance stats",
    description="Get overall attendance statistics for a course (teacher).",
)
def get_course_attendance_stats(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get overall attendance statistics for a course.
    
    **Teacher or Admin only.**
    """
    try:
        attendance_service = AttendanceService(db)
        
        # Check if teacher owns this course
        course_service = EnrollmentService(db)
        course = course_service.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        
        if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this course's attendance",
            )
        
        stats = attendance_service.get_overall_attendance_stats(course_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )