# ============================================================
# AETHER LINK - MODELS
# ============================================================
# Complete export of all models for easy importing
# ============================================================

from ..core.database import Base

# ============================================================
# USER & AUTH
# ============================================================
from .user import User, UserRole
from .refresh_token import RefreshToken
from .user_session import UserSession
from .password_reset import PasswordReset
from .audit_log import AuditLog, AuditEventType, AuditSeverity

# ============================================================
# COURSE & SESSIONS
# ============================================================
from .course import Course, CourseStatus, CourseLevel, CourseCategory
from .session import Session, SessionStatus, SessionType
from .material import Material, MaterialType, MaterialVisibility

# ============================================================
# ENROLLMENT & ATTENDANCE
# ============================================================
from .enrollment import Enrollment, EnrollmentStatus, PaymentMethod, EnrollmentSource
from .attendance import Attendance, AttendanceStatus, MarkedBy
from .video_watch_progress import VideoWatchProgress, WatchStatus

# ============================================================
# PAYMENT & CERTIFICATE
# ============================================================
from .payment import Payment, PaymentStatus, PaymentMethod as PaymentMethodEnum, PaymentGateway, PaymentType
from .payment_audit import PaymentAuditLog
from .certificate import (
    Certificate, CertificateStatus, CertificateTemplate, 
    CertificateTemplateStatus, CertificateVerificationLog,
    CertificateVerificationMethod, CertificateGenerationMethod,
    CertificateSettings, CertificateBatch
)

# ============================================================
# APPLICATION & INVITATIONS
# ============================================================
from .application import Application, ApplicationStatus, ApplicationSource, ApplicationPriority
from .teacher_invitation import TeacherInvitation, InvitationStatus

# ============================================================
# ASSIGNMENTS
# ============================================================
from .assignment import (
    Assignment, AssignmentStatus, AssignmentType,
    Submission, SubmissionStatus, GradeStatus,
    AssignmentComment, GradebookEntry
)

# ============================================================
# FORUM
# ============================================================
from .forum import (
    ForumTopic, TopicStatus, TopicType,
    ForumReply, ReplyStatus,
    ForumReplyLike, ForumTopicFollow, ForumFlag
)

# ============================================================
# REVIEW & RATING
# ============================================================
from .review import Review, ReviewStatus, ReviewType, ReviewHelpfulVote, ReviewFlag, CourseReviewStats

# ============================================================
# NOTIFICATION & ANNOUNCEMENT
# ============================================================
from .notification import (
    Notification, NotificationType, NotificationPriority,
    NotificationChannel, NotificationStatus,
    NotificationPreference, NotificationTemplate, NotificationBatch
)
from .announcement import (
    Announcement, AnnouncementPriority, AnnouncementStatus,
    AnnouncementTargetType, AnnouncementRead, AnnouncementTemplate
)

# ============================================================
# LEARNING PATH & COUPON
# ============================================================
from .learning_path import (
    LearningPath, LearningPathStatus, LearningPathLevel,
    PathCourse, PathEnrollment, PathEnrollmentStatus, PathReview
)
from .coupon import Coupon, CouponType, CouponStatus, CouponTargetType, CouponUsage, CouponUsageStatus

# ============================================================
# CHAT SYSTEM
# ============================================================
from .chat import (
    Conversation, ConversationType,
    ConversationParticipant, ParticipantRole,
    Message, MessageType, MessageStatus,
    MessageReaction,
    CourseChatRoom, CourseChatMessage
)

# ============================================================
# SOFTWARE HOUSE
# ============================================================
from .client import (
    Client, ClientStatus, ClientType, ClientIndustry,
    ClientContact, ContactRole, ClientCommunication
)
from .project import (
    ClientProject, ProjectStatus, ProjectPriority, ProjectVisibility,
    ProjectAssignment, ProjectTask, TaskStatus, TaskPriority, TaskType,
    TaskComment, TaskTimeEntry
)
from .invoice import (
    Invoice, InvoiceStatus, InvoiceType, InvoicePaymentMethod,
    InvoiceItem, InvoicePayment, InvoiceSettings
)

# ============================================================
# AI HUB
# ============================================================
from .ai_agent import (
    AIAgent, AIAgentStatus, AIAgentPricingType, AIAgentCategory,
    AIAgentSubscription, AISubscriptionStatus,
    AITrainingData, AITrainingDataType,
    AIApiKey, AIApiKeyStatus, AIApiLog
)

# ============================================================
# EXPOSE ALL MODELS
# ============================================================

__all__ = [
    # Core
    "Base",
    
    # User & Auth
    "User",
    "UserRole",
    "RefreshToken",
    "UserSession",
    "PasswordReset",
    "AuditLog",
    "AuditEventType",
    "AuditSeverity",
    
    # Course & Sessions
    "Course",
    "CourseStatus",
    "CourseLevel",
    "CourseCategory",
    "Session",
    "SessionStatus",
    "SessionType",
    "Material",
    "MaterialType",
    "MaterialVisibility",
    
    # Enrollment & Attendance
    "Enrollment",
    "EnrollmentStatus",
    "PaymentMethod",
    "EnrollmentSource",
    "Attendance",
    "AttendanceStatus",
    "MarkedBy",
    "VideoWatchProgress",
    "WatchStatus",
    
    # Payment & Certificate
    "Payment",
    "PaymentStatus",
    "PaymentMethodEnum",
    "PaymentGateway",
    "PaymentType",
    "PaymentAuditLog",
    "Certificate",
    "CertificateStatus",
    "CertificateTemplate",
    "CertificateTemplateStatus",
    "CertificateVerificationLog",
    "CertificateVerificationMethod",
    "CertificateGenerationMethod",
    "CertificateSettings",
    "CertificateBatch",
    
    # Application & Invitations
    "Application",
    "ApplicationStatus",
    "ApplicationSource",
    "ApplicationPriority",
    "TeacherInvitation",
    "InvitationStatus",
    
    # Assignments
    "Assignment",
    "AssignmentStatus",
    "AssignmentType",
    "Submission",
    "SubmissionStatus",
    "GradeStatus",
    "AssignmentComment",
    "GradebookEntry",
    
    # Forum
    "ForumTopic",
    "TopicStatus",
    "TopicType",
    "ForumReply",
    "ReplyStatus",
    "ForumReplyLike",
    "ForumTopicFollow",
    "ForumFlag",
    
    # Review & Rating
    "Review",
    "ReviewStatus",
    "ReviewType",
    "ReviewHelpfulVote",
    "ReviewFlag",
    "CourseReviewStats",
    
    # Notification & Announcement
    "Notification",
    "NotificationType",
    "NotificationPriority",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationPreference",
    "NotificationTemplate",
    "NotificationBatch",
    "Announcement",
    "AnnouncementPriority",
    "AnnouncementStatus",
    "AnnouncementTargetType",
    "AnnouncementRead",
    "AnnouncementTemplate",
    
    # Learning Path & Coupon
    "LearningPath",
    "LearningPathStatus",
    "LearningPathLevel",
    "PathCourse",
    "PathEnrollment",
    "PathEnrollmentStatus",
    "PathReview",
    "Coupon",
    "CouponType",
    "CouponStatus",
    "CouponTargetType",
    "CouponUsage",
    "CouponUsageStatus",
    
    # Chat System
    "Conversation",
    "ConversationType",
    "ConversationParticipant",
    "ParticipantRole",
    "Message",
    "MessageType",
    "MessageStatus",
    "MessageReaction",
    "CourseChatRoom",
    "CourseChatMessage",
    
    # Software House
    "Client",
    "ClientStatus",
    "ClientType",
    "ClientIndustry",
    "ClientContact",
    "ContactRole",
    "ClientCommunication",
    "ClientProject",
    "ProjectStatus",
    "ProjectPriority",
    "ProjectVisibility",
    "ProjectAssignment",
    "ProjectTask",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "TaskComment",
    "TaskTimeEntry",
    "Invoice",
    "InvoiceStatus",
    "InvoiceType",
    "InvoicePaymentMethod",
    "InvoiceItem",
    "InvoicePayment",
    "InvoiceSettings",
    
    # AI Hub
    "AIAgent",
    "AIAgentStatus",
    "AIAgentPricingType",
    "AIAgentCategory",
    "AIAgentSubscription",
    "AISubscriptionStatus",
    "AITrainingData",
    "AITrainingDataType",
    "AIApiKey",
    "AIApiKeyStatus",
    "AIApiLog",
]