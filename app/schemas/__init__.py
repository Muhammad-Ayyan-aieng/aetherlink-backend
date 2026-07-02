# ============================================================
# AETHER LINK - SCHEMAS
# ============================================================

# Auth Schemas
from .auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshToken,
    TokenData,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
    EmailVerificationConfirm,
    LogoutResponse,
)

# User Schemas
from .user import (
    UserRoleEnum,
    UserResponse,
    UserUpdate,
    UserRoleUpdate,
    UserStatusUpdate,
    UserListResponse,
)

# Course Schemas
from .course import (
    CourseStatusEnum,
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    SessionSummary,
    CourseDetailResponse,
    CourseListResponse,
)

# Session Schemas
from .session import (
    SessionStatusEnum,
    SessionBase,
    SessionCreate,
    SessionUpdate,
    RecordingAdd,
    SessionResponse,
    SessionDetailResponse,
    SessionListResponse,
)

# Enrollment Schemas
from .enrollment import (
    EnrollmentStatusEnum,
    PaymentMethodEnum,
    EnrollmentCreate,
    EnrollmentUpdate,
    PaymentVerification,
    ProgressUpdate,
    EnrollmentResponse,
    EnrollmentDetailResponse,
    StudentEnrollmentResponse,
    EnrollmentListResponse,
)

# Attendance Schemas ⭐ CRITICAL
from .attendance import (
    AttendanceStatusEnum,
    AttendanceMark,
    AttendanceUpdate,
    WatchRecording,
    BulkAttendanceMark,
    AttendanceResponse,
    MissedSessionResponse,
    AttendanceSummary,
    StudentAttendanceSummary,
    CourseAttendanceResponse,
    AttendanceListResponse,
)

# Payment Schemas
from .payment import (
    PaymentStatusEnum,
    PaymentMethodEnum as PaymentMethodSchemaEnum,
    PaymentInitiate,
    PaymentUploadScreenshot,
    PaymentVerify,
    PaymentReject,
    PaymentResponse,
    PaymentHistoryResponse,
    PaymentListResponse,
    PaymentSummary,
)

# Material Schemas
from .material import (
    MaterialTypeEnum,
    MaterialUpload,
    MaterialUpdate,
    MaterialResponse,
    MaterialListResponse,
)

# Invitation Schemas
from .invitation import (
    InviteTeacher,
    AcceptInvitation,
    ResendInvitation,
    InvitationResponse,
    InvitationDetailResponse,
    InvitationListResponse,
    InvitationSummary,
)

# ============================================================
# EXPOSE ALL SCHEMAS
# ============================================================

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "RefreshToken",
    "TokenData",
    "PasswordChange",
    "PasswordReset",
    "PasswordResetConfirm",
    "EmailVerification",
    "EmailVerificationConfirm",
    "LogoutResponse",
    
    # User
    "UserRoleEnum",
    "UserResponse",
    "UserUpdate",
    "UserRoleUpdate",
    "UserStatusUpdate",
    "UserListResponse",
    
    # Course
    "CourseStatusEnum",
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "SessionSummary",
    "CourseDetailResponse",
    "CourseListResponse",
    
    # Session
    "SessionStatusEnum",
    "SessionBase",
    "SessionCreate",
    "SessionUpdate",
    "RecordingAdd",
    "SessionResponse",
    "SessionDetailResponse",
    "SessionListResponse",
    
    # Enrollment
    "EnrollmentStatusEnum",
    "PaymentMethodEnum",
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "PaymentVerification",
    "ProgressUpdate",
    "EnrollmentResponse",
    "EnrollmentDetailResponse",
    "StudentEnrollmentResponse",
    "EnrollmentListResponse",
    
    # Attendance ⭐
    "AttendanceStatusEnum",
    "AttendanceMark",
    "AttendanceUpdate",
    "WatchRecording",
    "BulkAttendanceMark",
    "AttendanceResponse",
    "MissedSessionResponse",
    "AttendanceSummary",
    "StudentAttendanceSummary",
    "CourseAttendanceResponse",
    "AttendanceListResponse",
    
    # Payment
    "PaymentStatusEnum",
    "PaymentMethodSchemaEnum",
    "PaymentInitiate",
    "PaymentUploadScreenshot",
    "PaymentVerify",
    "PaymentReject",
    "PaymentResponse",
    "PaymentHistoryResponse",
    "PaymentListResponse",
    "PaymentSummary",
    
    # Material
    "MaterialTypeEnum",
    "MaterialUpload",
    "MaterialUpdate",
    "MaterialResponse",
    "MaterialListResponse",
    
    # Invitation
    "InviteTeacher",
    "AcceptInvitation",
    "ResendInvitation",
    "InvitationResponse",
    "InvitationDetailResponse",
    "InvitationListResponse",
    "InvitationSummary",
]