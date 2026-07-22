# ============================================================
# AETHER LINK - ASSIGNMENT SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# ASSIGNMENT ENUMS
# ============================================================

class AssignmentTypeEnum(str, Enum):
    """Assignment type enumeration."""
    HOMEWORK = "homework"
    QUIZ = "quiz"
    PROJECT = "project"
    EXAM = "exam"
    LAB = "lab"
    ESSAY = "essay"
    PRESENTATION = "presentation"
    OTHER = "other"


class AssignmentStatusEnum(str, Enum):
    """Assignment status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


class SubmissionStatusEnum(str, Enum):
    """Submission status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    GRADED = "graded"
    RESUBMITTED = "resubmitted"
    LATE = "late"
    REJECTED = "rejected"
    EXCUSED = "excused"


class GradeStatusEnum(str, Enum):
    """Grade status enumeration."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    EXEMPT = "exempt"


# ============================================================
# BASE SCHEMA
# ============================================================

class AssignmentBase(BaseModel):
    """Base assignment schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# ASSIGNMENT CREATE SCHEMA
# ============================================================

class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    session_id: Optional[int] = Field(default=None, gt=0, description="Session ID (optional)")
    
    title: str = Field(..., min_length=3, max_length=255, description="Assignment title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Assignment description")
    instructions: Optional[str] = Field(default=None, max_length=5000, description="Assignment instructions")
    
    assignment_type: AssignmentTypeEnum = Field(
        default=AssignmentTypeEnum.HOMEWORK,
        description="Assignment type"
    )
    
    due_date: datetime = Field(..., description="Due date and time")
    available_from: Optional[datetime] = Field(default=None, description="Available from date")
    available_until: Optional[datetime] = Field(default=None, description="Available until date")
    grace_period_minutes: int = Field(default=0, ge=0, description="Grace period in minutes")
    
    max_score: int = Field(default=100, ge=1, description="Maximum score")
    passing_score: int = Field(default=60, ge=0, le=100, description="Passing score")
    weight: float = Field(default=1.0, ge=0, le=10, description="Weight for course grade")
    max_attempts: int = Field(default=1, ge=1, le=10, description="Maximum attempts")
    
    file_required: bool = Field(default=False, description="Is file upload required?")
    text_required: bool = Field(default=False, description="Is text submission required?")
    allowed_file_types: Optional[List[str]] = Field(
        default=None,
        description="Allowed file types (e.g., ['pdf', 'docx'])"
    )
    max_file_size: int = Field(default=10485760, ge=0, description="Max file size in bytes")
    
    plagiarism_check_enabled: bool = Field(default=False, description="Enable plagiarism check")
    plagiarism_threshold: int = Field(default=30, ge=0, le=100, description="Plagiarism threshold percentage")
    
    status: AssignmentStatusEnum = Field(
        default=AssignmentStatusEnum.DRAFT,
        description="Assignment status"
    )
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: datetime) -> datetime:
        """Validate due date is in the future."""
        if v < datetime.now():
            raise ValueError('Due date must be in the future')
        return v


# ============================================================
# ASSIGNMENT UPDATE SCHEMA
# ============================================================

class AssignmentUpdate(AssignmentBase):
    """Schema for updating an assignment."""
    
    title: Optional[str] = Field(default=None, min_length=3, max_length=255, description="Assignment title")
    description: Optional[str] = Field(default=None, max_length=5000, description="Assignment description")
    instructions: Optional[str] = Field(default=None, max_length=5000, description="Assignment instructions")
    
    assignment_type: Optional[AssignmentTypeEnum] = Field(default=None, description="Assignment type")
    
    due_date: Optional[datetime] = Field(default=None, description="Due date and time")
    available_from: Optional[datetime] = Field(default=None, description="Available from date")
    available_until: Optional[datetime] = Field(default=None, description="Available until date")
    grace_period_minutes: Optional[int] = Field(default=None, ge=0, description="Grace period in minutes")
    
    max_score: Optional[int] = Field(default=None, ge=1, description="Maximum score")
    passing_score: Optional[int] = Field(default=None, ge=0, le=100, description="Passing score")
    weight: Optional[float] = Field(default=None, ge=0, le=10, description="Weight")
    max_attempts: Optional[int] = Field(default=None, ge=1, le=10, description="Maximum attempts")
    
    file_required: Optional[bool] = Field(default=None, description="Is file upload required?")
    text_required: Optional[bool] = Field(default=None, description="Is text submission required?")
    allowed_file_types: Optional[List[str]] = Field(default=None, description="Allowed file types")
    max_file_size: Optional[int] = Field(default=None, ge=0, description="Max file size in bytes")
    
    plagiarism_check_enabled: Optional[bool] = Field(default=None, description="Enable plagiarism check")
    plagiarism_threshold: Optional[int] = Field(default=None, ge=0, le=100, description="Plagiarism threshold")
    
    status: Optional[AssignmentStatusEnum] = Field(default=None, description="Assignment status")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is in the future."""
        if v and v < datetime.now():
            raise ValueError('Due date must be in the future')
        return v


# ============================================================
# ASSIGNMENT PUBLISH SCHEMA
# ============================================================

class AssignmentPublish(AssignmentBase):
    """Schema for publishing an assignment."""
    
    publish: bool = Field(..., description="True to publish, False to unpublish")
    notify_students: bool = Field(default=True, description="Notify students via email")


# ============================================================
# ASSIGNMENT SUBMIT SCHEMA
# ============================================================

class AssignmentSubmit(AssignmentBase):
    """Schema for submitting an assignment."""
    
    assignment_id: int = Field(..., gt=0, description="Assignment ID")
    content: Optional[str] = Field(default=None, max_length=10000, description="Text submission content")
    file_url: Optional[str] = Field(default=None, max_length=500, description="File submission URL")
    file_name: Optional[str] = Field(default=None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, max_length=100, description="MIME type")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate at least one of content or file_url is provided."""
        return v


# ============================================================
# ASSIGNMENT RESUBMIT SCHEMA
# ============================================================

class AssignmentResubmit(AssignmentBase):
    """Schema for resubmitting an assignment."""
    
    assignment_id: int = Field(..., gt=0, description="Assignment ID")
    content: Optional[str] = Field(default=None, max_length=10000, description="Text submission content")
    file_url: Optional[str] = Field(default=None, max_length=500, description="File submission URL")
    file_name: Optional[str] = Field(default=None, max_length=255, description="Original file name")
    file_size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, max_length=100, description="MIME type")
    revision_notes: Optional[str] = Field(default=None, max_length=500, description="Revision notes")


# ============================================================
# ASSIGNMENT GRADE SCHEMA (Teacher)
# ============================================================

class AssignmentGrade(AssignmentBase):
    """Schema for grading a submission."""
    
    submission_id: int = Field(..., gt=0, description="Submission ID")
    score: int = Field(..., ge=0, description="Score awarded")
    feedback: Optional[str] = Field(default=None, max_length=2000, description="Feedback text")
    notes: Optional[str] = Field(default=None, max_length=500, description="Internal notes (not shown to student)")


# ============================================================
# ASSIGNMENT RESPONSE SCHEMA
# ============================================================

class AssignmentResponse(AssignmentBase):
    """Schema for assignment response."""
    
    id: int = Field(..., description="Assignment ID")
    course_id: int = Field(..., description="Course ID")
    course_title: Optional[str] = Field(default=None, description="Course title")
    session_id: Optional[int] = Field(default=None, description="Session ID")
    
    title: str = Field(..., description="Assignment title")
    description: Optional[str] = Field(default=None, description="Assignment description")
    instructions: Optional[str] = Field(default=None, description="Assignment instructions")
    
    assignment_type: str = Field(..., description="Assignment type")
    display_type: str = Field(..., description="Human-readable type")
    
    status: str = Field(..., description="Assignment status")
    display_status: str = Field(..., description="Human-readable status")
    
    due_date: datetime = Field(..., description="Due date")
    available_from: Optional[datetime] = Field(default=None, description="Available from")
    available_until: Optional[datetime] = Field(default=None, description="Available until")
    is_overdue: bool = Field(..., description="Is overdue")
    is_available: bool = Field(..., description="Is available")
    days_until_due: int = Field(..., description="Days until due")
    hours_until_due: float = Field(..., description="Hours until due")
    
    max_score: int = Field(..., description="Maximum score")
    passing_score: int = Field(..., description="Passing score")
    weight: float = Field(..., description="Weight")
    max_attempts: int = Field(..., description="Maximum attempts")
    
    file_required: bool = Field(..., description="Is file upload required?")
    text_required: bool = Field(..., description="Is text submission required?")
    allowed_file_types: Optional[List[str]] = Field(default=None, description="Allowed file types")
    max_file_size: int = Field(..., description="Max file size in bytes")
    
    total_submissions: int = Field(default=0, description="Total submissions")
    graded_count: int = Field(default=0, description="Graded submissions count")
    average_score: float = Field(default=0.0, description="Average score")
    
    created_by: int = Field(..., description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# SUBMISSION RESPONSE SCHEMA
# ============================================================

class SubmissionResponse(AssignmentBase):
    """Schema for submission response."""
    
    id: int = Field(..., description="Submission ID")
    assignment_id: int = Field(..., description="Assignment ID")
    assignment_title: Optional[str] = Field(default=None, description="Assignment title")
    
    student_id: int = Field(..., description="Student ID")
    student_name: Optional[str] = Field(default=None, description="Student name")
    enrollment_id: int = Field(..., description="Enrollment ID")
    
    content: Optional[str] = Field(default=None, description="Text submission")
    file_url: Optional[str] = Field(default=None, description="File URL")
    file_name: Optional[str] = Field(default=None, description="Original file name")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    
    status: str = Field(..., description="Submission status")
    display_status: str = Field(..., description="Human-readable status")
    
    attempt_number: int = Field(..., description="Attempt number")
    is_late: bool = Field(..., description="Is late submission")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    
    score: Optional[int] = Field(default=None, description="Score awarded")
    feedback: Optional[str] = Field(default=None, description="Feedback text")
    grade_status: str = Field(..., description="Grade status")
    has_passed: bool = Field(..., description="Has passed")
    display_grade: str = Field(..., description="Display grade")
    pass_fail_display: str = Field(..., description="Pass/Fail display")
    
    graded_by: Optional[int] = Field(default=None, description="Graded by user ID")
    graded_by_name: Optional[str] = Field(default=None, description="Graded by user name")
    graded_at: Optional[datetime] = Field(default=None, description="Grading timestamp")
    
    plagiarism_score: Optional[int] = Field(default=None, description="Plagiarism score")
    plagiarism_report_url: Optional[str] = Field(default=None, description="Plagiarism report URL")
    
    previous_submission_id: Optional[int] = Field(default=None, description="Previous submission ID")
    revision_notes: Optional[str] = Field(default=None, description="Revision notes")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# ASSIGNMENT DETAIL RESPONSE
# ============================================================

class AssignmentDetailResponse(AssignmentResponse):
    """Schema for assignment detail response with submissions."""
    
    submissions: Optional[List[SubmissionResponse]] = Field(
        default=None,
        description="List of submissions"
    )
    
    # NEW: Student-specific info
    user_submission: Optional[SubmissionResponse] = Field(
        default=None,
        description="Current user's submission"
    )
    user_has_submitted: bool = Field(default=False, description="User has submitted")
    user_can_submit: bool = Field(default=True, description="User can submit")
    user_remaining_attempts: int = Field(default=0, description="Remaining attempts")


# ============================================================
# ASSIGNMENT LIST REQUEST (Filters)
# ============================================================

class AssignmentListRequest(AssignmentBase):
    """Schema for assignment list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by title")
    status: Optional[AssignmentStatusEnum] = Field(default=None, description="Filter by status")
    assignment_type: Optional[AssignmentTypeEnum] = Field(default=None, description="Filter by type")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    session_id: Optional[int] = Field(default=None, description="Filter by session")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# ASSIGNMENT LIST RESPONSE
# ============================================================

class AssignmentListResponse(AssignmentBase):
    """Schema for paginated assignment list response."""
    
    assignments: List[AssignmentResponse] = Field(..., description="List of assignments")
    total: int = Field(..., description="Total assignments")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# SUBMISSION LIST REQUEST (Filters)
# ============================================================

class SubmissionListRequest(AssignmentBase):
    """Schema for submission list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by student name")
    status: Optional[SubmissionStatusEnum] = Field(default=None, description="Filter by status")
    grade_status: Optional[GradeStatusEnum] = Field(default=None, description="Filter by grade status")
    is_late: Optional[bool] = Field(default=None, description="Filter by late submissions")
    assignment_id: Optional[int] = Field(default=None, description="Filter by assignment")
    student_id: Optional[int] = Field(default=None, description="Filter by student")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# SUBMISSION LIST RESPONSE
# ============================================================

class SubmissionListResponse(AssignmentBase):
    """Schema for paginated submission list response."""
    
    submissions: List[SubmissionResponse] = Field(..., description="List of submissions")
    total: int = Field(..., description="Total submissions")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# ASSIGNMENT STATISTICS
# ============================================================

class AssignmentStatistics(AssignmentBase):
    """Schema for assignment statistics."""
    
    total_assignments: int = Field(..., description="Total assignments")
    draft: int = Field(..., description="Draft assignments")
    published: int = Field(..., description="Published assignments")
    open: int = Field(..., description="Open assignments")
    closed: int = Field(..., description="Closed assignments")
    archived: int = Field(..., description="Archived assignments")
    
    # NEW: Submission stats
    total_submissions: int = Field(..., description="Total submissions")
    graded_submissions: int = Field(..., description="Graded submissions")
    pending_grading: int = Field(..., description="Pending grading")
    late_submissions: int = Field(..., description="Late submissions")
    resubmissions: int = Field(..., description="Resubmissions")
    
    # NEW: Grade stats
    passed_count: int = Field(..., description="Passed submissions")
    failed_count: int = Field(..., description="Failed submissions")
    average_score: float = Field(..., description="Average score")
    pass_rate: float = Field(..., description="Pass rate percentage")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Assignments by type"
    )


# ============================================================
# ASSIGNMENT COMMENT SCHEMAS
# ============================================================

class AssignmentCommentCreate(AssignmentBase):
    """Schema for creating an assignment comment."""
    
    submission_id: int = Field(..., gt=0, description="Submission ID")
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    is_private: bool = Field(default=False, description="Teacher-only comment")


class AssignmentCommentResponse(AssignmentBase):
    """Schema for assignment comment response."""
    
    id: int = Field(..., description="Comment ID")
    submission_id: int = Field(..., description="Submission ID")
    user_id: int = Field(..., description="User ID")
    user_name: Optional[str] = Field(default=None, description="User name")
    user_role: Optional[str] = Field(default=None, description="User role")
    content: str = Field(..., description="Comment content")
    is_private: bool = Field(..., description="Is private comment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "AssignmentTypeEnum",
    "AssignmentStatusEnum",
    "SubmissionStatusEnum",
    "GradeStatusEnum",
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentPublish",
    "AssignmentSubmit",
    "AssignmentResubmit",
    "AssignmentGrade",
    "AssignmentResponse",
    "SubmissionResponse",
    "AssignmentDetailResponse",
    "AssignmentListRequest",
    "AssignmentListResponse",
    "SubmissionListRequest",
    "SubmissionListResponse",
    "AssignmentStatistics",
    "AssignmentCommentCreate",
    "AssignmentCommentResponse",
]