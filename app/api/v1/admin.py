# ============================================================
# AETHER LINK - ADMIN API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.dependencies import get_current_admin_user, rate_limiter, get_current_user
from ...services.user_service import UserService
from ...services.course_service import CourseService
from ...services.enrollment_service import EnrollmentService
from ...services.payment_service import PaymentService
from ...services.attendance_service import AttendanceService
from ...services.session_service import SessionService
from ...models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get(
    "/dashboard",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get admin dashboard",
    description="Get admin dashboard overview.",
)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get admin dashboard overview.
    
    **Admin only.**
    """
    try:
        user_service = UserService(db)
        course_service = CourseService(db)
        enrollment_service = EnrollmentService(db)
        payment_service = PaymentService(db)
        attendance_service = AttendanceService(db)
        session_service = SessionService(db)
        
        # User stats
        user_stats = user_service.get_user_stats()
        
        # Course stats
        course_stats = course_service.get_course_stats(current_user.id)
        
        # Enrollment stats
        enrollment_stats = enrollment_service.get_enrollment_stats(current_user.id)
        
        # Payment stats
        payment_stats = payment_service.get_dashboard_stats(current_user.id)
        
        # Attendance stats (overall)
        # Get all courses and calculate attendance
        courses = course_service.course_repo.get_all()
        total_sessions = 0
        total_attendance = 0
        total_missed = 0
        
        for course in courses[0]:
            if course.id:
                try:
                    stats = attendance_service.get_overall_attendance_stats(course.id)
                    total_sessions += stats.get("total_sessions", 0)
                    total_attendance += stats.get("total_present", 0) + stats.get("total_made_up", 0)
                    total_missed += stats.get("total_missed", 0)
                except:
                    pass
        
        avg_attendance = (total_attendance / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            "users": {
                "total": user_stats.get("total", 0),
                "active": user_stats.get("active", 0),
                "inactive": user_stats.get("inactive", 0),
                "teachers": user_stats.get("teachers", 0),
                "students": user_stats.get("students", 0),
                "admins": user_stats.get("admins", 0),
            },
            "courses": {
                "total": course_stats.get("total", 0),
                "published": course_stats.get("published", 0),
                "drafts": course_stats.get("drafts", 0),
                "archived": course_stats.get("archived", 0),
                "featured": course_stats.get("featured", 0),
            },
            "enrollments": {
                "total": enrollment_stats.get("total", 0),
                "active": enrollment_stats.get("active", 0),
                "completed": enrollment_stats.get("completed", 0),
                "pending": enrollment_stats.get("pending", 0),
                "payment_verification": enrollment_stats.get("payment_verification", 0),
            },
            "payments": {
                "today_revenue": payment_stats.get("today_revenue", 0),
                "month_revenue": payment_stats.get("month_revenue", 0),
                "total_revenue": payment_stats.get("total_revenue", 0),
                "total_transactions": payment_stats.get("total_transactions", 0),
                "pending_verification": payment_stats.get("pending_verification", 0),
                "recent_transactions": payment_stats.get("recent_transactions", []),
            },
            "attendance": {
                "total_sessions": total_sessions,
                "total_attendance": total_attendance,
                "avg_attendance_rate": round(avg_attendance, 2),
                "missed_sessions": total_missed,
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: USER MANAGEMENT
# ============================================================

@router.get(
    "/users",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get users for admin",
    description="Get user management data (admin only).",
)
def get_admin_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get users for admin management.
    
    **Admin only.**
    """
    try:
        user_service = UserService(db)
        
        active_only = status != "inactive"
        if status == "inactive":
            active_only = False
        
        result = user_service.get_users(
            skip=skip,
            limit=limit,
            role=UserRole(role) if role else None,
            active_only=active_only,
            search=search,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: COURSE MANAGEMENT
# ============================================================

@router.get(
    "/courses",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get courses for admin",
    description="Get course management data (admin only).",
)
def get_admin_courses(
    status: Optional[str] = Query(None, description="Filter by status"),
    featured: Optional[bool] = Query(None, description="Filter by featured"),
    search: Optional[str] = Query(None, description="Search by title"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get courses for admin management.
    
    **Admin only.**
    """
    try:
        course_service = CourseService(db)
        
        if search:
            courses = course_service.search_courses(query=search)
            total = len(courses)
            courses = courses[skip:skip + limit]
        else:
            courses, total = course_service.course_repo.get_all(skip=skip, limit=limit)
        
        return {
            "courses": courses,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: PAYMENT MANAGEMENT
# ============================================================

@router.get(
    "/payments",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get payments for admin",
    description="Get payment management data (admin only).",
)
def get_admin_payments(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get payments for admin management.
    
    **Admin only.**
    """
    try:
        payment_service = PaymentService(db)
        
        if status == "pending":
            pending = payment_service.get_pending_payments(current_user.id)
            return {
                "payments": pending,
                "total": len(pending),
                "page": 1,
                "page_size": len(pending),
                "total_pages": 1,
            }
        else:
            # Get all payments - simplified
            # In production, use proper pagination
            payments = payment_service.payment_repo.get_all()
            total = payments[1] if isinstance(payments, tuple) else 0
            payment_list = payments[0] if isinstance(payments, tuple) else payments
            
            return {
                "payments": payment_list[skip:skip + limit],
                "total": total,
                "page": skip // limit + 1 if limit > 0 else 1,
                "page_size": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
            }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: ATTENDANCE REPORT
# ============================================================

@router.get(
    "/reports/attendance",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get attendance report",
    description="Get attendance report (admin only).",
)
def get_attendance_report(
    course_id: Optional[int] = Query(None, description="Filter by course"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Output format: json, csv"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get attendance report.
    
    **Admin only.**
    """
    try:
        attendance_service = AttendanceService(db)
        course_service = CourseService(db)
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        
        if course_id:
            # Get attendance for specific course
            stats = attendance_service.get_overall_attendance_stats(course_id)
            course = course_service.get_course(course_id)
            
            return {
                "course_id": course_id,
                "course_title": course.title if course else None,
                "total_students": stats.get("total_students", 0),
                "attendance_rate": stats.get("overall_attendance_rate", 0),
                "total_present": stats.get("total_present", 0),
                "total_missed": stats.get("total_missed", 0),
                "total_made_up": stats.get("total_made_up", 0),
            }
        else:
            # Get attendance for all courses
            courses = course_service.course_repo.get_published()
            results = []
            
            for course in courses[0]:
                if course.id:
                    try:
                        stats = attendance_service.get_overall_attendance_stats(course.id)
                        results.append({
                            "course_id": course.id,
                            "course_title": course.title,
                            "total_students": stats.get("total_students", 0),
                            "attendance_rate": stats.get("overall_attendance_rate", 0),
                        })
                    except:
                        pass
            
            return {
                "courses": results,
                "total_courses": len(results),
            }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: REVENUE REPORT
# ============================================================

@router.get(
    "/reports/revenue",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get revenue report",
    description="Get revenue report (admin only).",
)
def get_revenue_report(
    period: str = Query("month", description="Period: day, week, month, quarter, year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get revenue report.
    
    **Admin only.**
    """
    try:
        payment_service = PaymentService(db)
        
        # Get revenue stats
        stats = payment_service.get_revenue_stats(current_user.id)
        revenue_by_course = payment_service.get_revenue_by_course(current_user.id)
        
        return {
            "summary": stats,
            "by_course": revenue_by_course,
            "period": period,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: ENGAGEMENT REPORT
# ============================================================

@router.get(
    "/reports/engagement",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get engagement report",
    description="Get student engagement report (admin only).",
)
def get_engagement_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get student engagement report.
    
    **Admin only.**
    """
    try:
        user_service = UserService(db)
        enrollment_service = EnrollmentService(db)
        attendance_service = AttendanceService(db)
        
        # Get all students
        students = user_service.get_students(active_only=True)
        
        engagement_data = []
        for student in students:
            # Get attendance summary
            summary = attendance_service.get_attendance_summary(student.id)
            enrollments = enrollment_service.get_student_enrollments(student.id)
            
            engagement_data.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "student_email": student.email,
                "enrollments": len(enrollments.get("enrollments", [])),
                "attendance": summary.get("overall_attendance", 0),
                "total_present": summary.get("total_present", 0),
                "total_missed": summary.get("total_missed", 0),
                "total_made_up": summary.get("total_made_up", 0),
            })
        
        return {
            "students": engagement_data,
            "total_students": len(engagement_data),
            "average_attendance": sum(s["attendance"] for s in engagement_data) / len(engagement_data) if engagement_data else 0,
            "average_enrollments": sum(s["enrollments"] for s in engagement_data) / len(engagement_data) if engagement_data else 0,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )