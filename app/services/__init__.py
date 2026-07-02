# ============================================================
# AETHER LINK - SERVICES
# ============================================================

from .auth_service import AuthService
from .user_service import UserService
from .course_service import CourseService
from .session_service import SessionService
from .enrollment_service import EnrollmentService
from .attendance_service import AttendanceService  # ⭐ CRITICAL
from .payment_service import PaymentService
from .material_service import MaterialService
from .invitation_service import InvitationService

# ============================================================
# EXPOSE ALL SERVICES
# ============================================================

__all__ = [
    "AuthService",
    "UserService",
    "CourseService",
    "SessionService",
    "EnrollmentService",
    "AttendanceService",  # ⭐ CRITICAL
    "PaymentService",
    "MaterialService",
    "InvitationService",
]