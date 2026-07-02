# ============================================================
# AETHER LINK - MODELS
# ============================================================

from ..core.database import Base

# User & Roles
from .user import User, UserRole

# Course
from .course import Course, CourseStatus

# Session (file is sessions.py)
from .sessions import Session, SessionStatus

# Enrollment
from .enrollment import Enrollment, EnrollmentStatus, PaymentMethod

# Attendance ⭐ CRITICAL
from .attendance import Attendance, AttendanceStatus

# Payment (file is payments.py)
from .payments import Payment, PaymentStatus

# Course Materials
from .material import CourseMaterial

# Teacher Invitations (file is invitations.py)
from .invitations import TeacherInvitation

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
]