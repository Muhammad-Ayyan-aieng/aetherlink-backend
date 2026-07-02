# ============================================================
# AETHER LINK - REPOSITORIES
# ============================================================

# Base Repository
from .base import BaseRepository

# User Repository
from .user_repository import UserRepository

# Course Repository
from .course_repository import CourseRepository

# Session Repository
from .session_repository import SessionRepository

# Enrollment Repository
from .enrollment_repository import EnrollmentRepository

# ⭐ Attendance Repository (CRITICAL)
from .attendance_repository import AttendanceRepository

# Payment Repository
from .payment_repository import PaymentRepository

# Material Repository
from .material_repository import MaterialRepository

# Invitation Repository
from .invitation_repository import InvitationRepository

# ============================================================
# EXPOSE ALL REPOSITORIES
# ============================================================

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CourseRepository",
    "SessionRepository",
    "EnrollmentRepository",
    "AttendanceRepository",  # ⭐ CRITICAL
    "PaymentRepository",
    "MaterialRepository",
    "InvitationRepository",
]