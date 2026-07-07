# ============================================================
# AETHER LINK - ADMIN API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List, Any
from datetime import datetime, timedelta
import logging

# FIX 1: Add missing get_db import
from ...core.database import get_db
from ...core.dependencies import get_current_admin_user, get_current_user
from ...services.user_service import UserService
from ...services.course_service import CourseService
from ...services.enrollment_service import EnrollmentService
from ...services.payment_service import PaymentService
from ...services.attendance_service import AttendanceService
from ...services.session_service import SessionService
from ...models.user import User, UserRole
# FIX 2: Change 'payment' to 'payments' (plural)
from ...models.payments import Payment, PaymentStatus, PaymentMethod

logger = logging.getLogger(__name__)
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
        
        # User stats
        user_stats = user_service.get_user_stats()
        
        # Course stats
        course_stats = course_service.get_course_stats(current_user.id)
        
        # Enrollment stats
        enrollment_stats = enrollment_service.get_enrollment_stats(current_user.id)
        
        # Payment stats
        payment_stats = payment_service.get_dashboard_stats(current_user.id)
        
        # Attendance stats (overall)
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
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard: {str(e)}",
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
        
        if role and role not in ["student", "teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be: student, teacher, admin"
            )
        
        active_only = status != "inactive"
        if status == "inactive":
            active_only = False
        
        role_enum = None
        if role:
            try:
                role_enum = UserRole(role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}"
                )
        
        result = user_service.get_users(
            skip=skip,
            limit=limit,
            role=role_enum,
            active_only=active_only,
            search=search,
        )
        
        user_list = []
        for user in result.get("users", []):
            user_list.append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
                "profile_picture": user.profile_picture,
                "bio": user.bio,
                "role": user.role.value,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "last_login": user.last_login,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            })
        
        return {
            "users": user_list,
            "total": result.get("total", 0),
            "page": result.get("page", 1),
            "page_size": result.get("page_size", limit),
            "total_pages": result.get("total_pages", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}",
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
    status: Optional[str] = Query(None, description="Filter by status: draft, published, archived"),
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
        
        if status and status not in ["draft", "published", "archived"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be: draft, published, archived"
            )
        
        filters = {}
        if status:
            filters["status"] = status
        if featured is not None:
            filters["is_featured"] = featured
        
        if search:
            courses = course_service.search_courses(query=search)
            total = len(courses)
            courses = courses[skip:skip + limit]
        else:
            courses, total = course_service.course_repo.get_all(skip=skip, limit=limit, **filters)
        
        course_list = []
        for course in courses:
            teacher_name = None
            try:
                if course.teacher:
                    teacher_name = course.teacher.full_name
            except:
                pass
            
            course_list.append({
                "id": course.id,
                "title": course.title,
                "slug": course.slug,
                "description": course.description,
                "price": float(course.price) if course.price else 0,
                "thumbnail": course.thumbnail,
                "status": course.status.value if course.status else None,
                "is_featured": course.is_featured,
                "teacher_id": course.teacher_id,
                "teacher_name": teacher_name,
                "total_sessions": course.total_sessions,
                "meta_title": course.meta_title,
                "meta_description": course.meta_description,
                "meta_keywords": course.meta_keywords,
                "created_at": course.created_at,
                "updated_at": course.updated_at,
                "deleted_at": course.deleted_at,
            })
        
        return {
            "courses": course_list,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin courses error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching courses: {str(e)}",
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
    status: Optional[str] = Query(None, description="Filter by status: pending, awaiting_verification, verified, rejected, refunded"),
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
        # Validate status if provided
        valid_statuses = ["pending", "awaiting_verification", "verified", "rejected", "refunded"]
        if status and status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Build query with PaymentStatus enum
        query = db.query(Payment)
        
        if status:
            try:
                status_enum = PaymentStatus(status)
                query = query.filter(Payment.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid payment status: {status}"
                )
        
        total = query.count()
        payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
        
        payment_list = []
        for payment in payments:
            student_name = None
            student_email = None
            try:
                if payment.student:
                    student_name = payment.student.full_name
                    student_email = payment.student.email
            except:
                pass
            
            payment_list.append({
                "id": payment.id,
                "student_id": payment.student_id,
                "enrollment_id": payment.enrollment_id,
                "amount": float(payment.amount) if payment.amount else 0,
                "method": payment.method.value if payment.method else None,
                "status": payment.status.value if payment.status else None,
                "screenshot_url": payment.screenshot_url,
                "transaction_id": payment.transaction_id,
                "student_name": student_name,
                "student_email": student_email,
                "verified_by": payment.verified_by,
                "verified_at": payment.verified_at,
                "rejected_at": payment.rejected_at,
                "rejection_reason": payment.rejection_reason,
                "refunded_at": payment.refunded_at,
                "created_at": payment.created_at,
                "updated_at": payment.updated_at,
            })
        
        return {
            "payments": payment_list,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin payments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payments: {str(e)}",
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
        
        start = None
        end = None
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        if course_id:
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
                "generated_at": datetime.utcnow().isoformat(),
            }
        else:
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
                "generated_at": datetime.utcnow().isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attendance report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating attendance report: {str(e)}",
        )


# ============================================================
# ADMIN: REVENUE REPORT (FIXED)
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
        valid_periods = ["day", "week", "month", "quarter", "year"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # FIX: Explicit SELECT FROM to avoid SQL join ambiguity
        query = db.query(
            func.date_trunc(period, Payment.created_at).label("period"),
            func.sum(Payment.amount).label("total"),
            func.count(Payment.id).label("count")
        ).select_from(Payment)
        
        query = query.filter(Payment.status == PaymentStatus.VERIFIED)
        query = query.group_by(func.date_trunc(period, Payment.created_at))
        query = query.order_by(func.date_trunc(period, Payment.created_at).desc())
        query = query.limit(12)
        
        results = query.all()
        
        data = []
        for r in results:
            period_value = r.period.isoformat() if r.period else None
            total_amount = float(r.total) if r.total else 0.0
            count = r.count or 0
            data.append({
                "period": period_value,
                "total": total_amount,
                "count": count
            })
        
        total_revenue = sum(d["total"] for d in data)
        total_transactions = sum(d["count"] for d in data)
        
        return {
            "period": period,
            "data": data,
            "summary": {
                "total_revenue": total_revenue,
                "total_transactions": total_transactions,
                "periods_count": len(data)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revenue report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating revenue report: {str(e)}",
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
        
        students = user_service.get_students(active_only=True)
        
        engagement_data = []
        total_attendance = 0
        total_enrollments = 0
        
        for student in students:
            try:
                summary = attendance_service.get_attendance_summary(student.id)
                enrollments = enrollment_service.get_student_enrollments(student.id)
                
                attendance_rate = summary.get("overall_attendance", 0) or 0
                enroll_count = len(enrollments.get("enrollments", []))
                
                total_attendance += attendance_rate
                total_enrollments += enroll_count
                
                engagement_data.append({
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "student_email": student.email,
                    "enrollments": enroll_count,
                    "attendance_rate": attendance_rate,
                    "total_present": summary.get("total_present", 0),
                    "total_missed": summary.get("total_missed", 0),
                    "total_made_up": summary.get("total_made_up", 0),
                })
            except Exception as e:
                logger.warning(f"Error getting engagement for student {student.id}: {e}")
                continue
        
        student_count = len(engagement_data)
        avg_attendance = (total_attendance / student_count) if student_count > 0 else 0
        avg_enrollments = (total_enrollments / student_count) if student_count > 0 else 0
        
        return {
            "students": engagement_data,
            "total_students": student_count,
            "average_attendance_rate": round(avg_attendance, 2),
            "average_enrollments": round(avg_enrollments, 2),
            "generated_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Engagement report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating engagement report: {str(e)}",
        )