# ============================================================
# AETHER LINK - MODELS
# ============================================================

from ..core.database import Base

# User & Roles
from .user import User, UserRole

# Course
from .course import Course, CourseStatus

# Session
from .sessions import Session, SessionStatus

# Enrollment
from .enrollment import Enrollment, EnrollmentStatus, PaymentMethod

# Attendance ⭐ CRITICAL
from .attendance import Attendance, AttendanceStatus

# Payment
from .payments import Payment, PaymentStatus

# Course Materials
from .material import CourseMaterial

# Teacher Invitations
from .invitations import TeacherInvitation

# Applications
from .application import Application, ApplicationStatus  # ← ADD THIS
from .refresh_token import RefreshToken

# Payments
from .payments import Payment, PaymentStatus, PaymentMethod

# ============================================================
# EXPOSE ALL MODELS
# ============================================================

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Course",
    "CourseStatus",
    "Session",
    "SessionStatus",
    "Enrollment",
    "EnrollmentStatus",
    "PaymentMethod",
    "Attendance",
    "AttendanceStatus",
    "Payment",
    "PaymentStatus",
    "CourseMaterial",
    "TeacherInvitation",
    "Application",          # ← ADD THIS
    "ApplicationStatus",    # ← ADD THIS
    "RefreshToken",
]