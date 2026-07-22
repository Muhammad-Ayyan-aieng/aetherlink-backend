# ============================================================
# AETHER LINK - ASSIGNMENT MODEL
# ============================================================
# Purpose: Manage assignments, submissions, and grading
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, BigInteger, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class AssignmentType(str, enum.Enum):
    """Assignment type enumeration."""
    HOMEWORK = "homework"
    QUIZ = "quiz"
    PROJECT = "project"
    EXAM = "exam"
    LAB = "lab"
    ESSAY = "essay"
    PRESENTATION = "presentation"
    OTHER = "other"


class AssignmentStatus(str, enum.Enum):
    """Assignment status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


class SubmissionStatus(str, enum.Enum):
    """Submission status enumeration."""
    DRAFT = "draft"  # Student is working on it
    SUBMITTED = "submitted"  # Submitted for grading
    GRADED = "graded"  # Graded by teacher
    RESUBMITTED = "resubmitted"  # Resubmitted after feedback
    LATE = "late"  # Submitted after due date
    REJECTED = "rejected"  # Rejected for resubmission
    EXCUSED = "excused"  # Excused from assignment


class GradeStatus(str, enum.Enum):
    """Grade status enumeration."""
    PENDING = "pending"  # Not yet graded
    PASSED = "passed"
    FAILED = "failed"
    EXEMPT = "exempt"


# ============================================================
# 1. ASSIGNMENT MODEL
# ============================================================

class Assignment(Base):
    __tablename__ = "assignments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Assignment type
    assignment_type = Column(
        String(50),
        default=AssignmentType.HOMEWORK.value,
        nullable=False
    )
    
    # ============================================================
    # DUE DATES
    # ============================================================
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Available date (when students can start)
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Grace period (minutes after due date)
    grace_period_minutes = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # SCORING
    # ============================================================
    max_score = Column(Integer, default=100, nullable=False)
    passing_score = Column(Integer, default=60, nullable=False)
    
    # NEW: Weight (for overall course grade)
    weight = Column(DECIMAL(5, 2), default=1.00, nullable=False)
    
    # NEW: Number of attempts allowed
    max_attempts = Column(Integer, default=1, nullable=False)
    
    # ============================================================
    # SUBMISSION SETTINGS
    # ============================================================
    file_required = Column(Boolean, default=False, nullable=False)
    text_required = Column(Boolean, default=False, nullable=False)
    
    # Allowed file types
    allowed_file_types = Column(JSON, nullable=True)
    # Example: ["pdf", "docx", "pptx", "zip"]
    
    # Max file size
    max_file_size = Column(BigInteger, default=10485760, nullable=False)  # 10MB default
    
    # ============================================================
    # PLAGIARISM CHECK
    # ============================================================
    plagiarism_check_enabled = Column(Boolean, default=False, nullable=False)
    plagiarism_threshold = Column(Integer, default=30, nullable=False)  # Percentage
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=AssignmentStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # STATISTICS (Cached)
    # ============================================================
    total_submissions = Column(Integer, default=0, nullable=False)
    graded_count = Column(Integer, default=0, nullable=False)
    average_score = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    
    # ============================================================
    # METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_assignments_course_status', 'course_id', 'status'),
        Index('ix_assignments_due_date', 'due_date'),
        Index('ix_assignments_type', 'assignment_type'),
        Index('ix_assignments_published', 'status'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship(
        "Course",
        back_populates="assignments",
        foreign_keys=[course_id]
    )
    
    session = relationship(
        "Session",
        foreign_keys=[session_id],
        uselist=False
    )
    
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        uselist=False
    )
    
    submissions = relationship(
        "Submission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Assignment {self.id}: {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_draft(self) -> bool:
        """Check if assignment is draft."""
        return self.status == AssignmentStatus.DRAFT.value
    
    @property
    def is_published(self) -> bool:
        """Check if assignment is published."""
        return self.status == AssignmentStatus.PUBLISHED.value
    
    @property
    def is_open(self) -> bool:
        """Check if assignment is open."""
        return self.status == AssignmentStatus.OPEN.value
    
    @property
    def is_closed(self) -> bool:
        """Check if assignment is closed."""
        return self.status == AssignmentStatus.CLOSED.value
    
    @property
    def is_archived(self) -> bool:
        """Check if assignment is archived."""
        return self.status == AssignmentStatus.ARCHIVED.value
    
    @property
    def is_overdue(self) -> bool:
        """Check if assignment is overdue."""
        if self.due_date is None:
            return False
        return self.due_date <= func.now()
    
    @property
    def is_available(self) -> bool:
        """Check if assignment is available to students."""
        if not self.is_open:
            return False
        if self.available_from and self.available_from > func.now():
            return False
        if self.available_until and self.available_until < func.now():
            return False
        return True
    
    @property
    def days_until_due(self) -> int:
        """Get days until due date."""
        if self.due_date is None:
            return -1
        delta = self.due_date - func.now()
        return max(0, delta.days)
    
    @property
    def hours_until_due(self) -> float:
        """Get hours until due date."""
        if self.due_date is None:
            return -1.0
        delta = self.due_date - func.now()
        return max(0.0, delta.total_seconds() / 3600)
    
    @property
    def display_type(self) -> str:
        """Get human-readable assignment type."""
        type_map = {
            "homework": "Homework",
            "quiz": "Quiz",
            "project": "Project",
            "exam": "Exam",
            "lab": "Lab",
            "essay": "Essay",
            "presentation": "Presentation",
            "other": "Other",
        }
        return type_map.get(self.assignment_type, "Assignment")
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_draft:
            return "Draft"
        elif self.is_published:
            return "Published"
        elif self.is_open:
            return "Open"
        elif self.is_closed:
            return "Closed"
        elif self.is_archived:
            return "Archived"
        return "Unknown"
    
    @property
    def submission_rate(self) -> float:
        """Calculate submission rate."""
        if self.total_submissions == 0:
            return 0.0
        # This would need total enrolled students from course
        return self.total_submissions  # Placeholder
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.graded_count == 0:
            return 0.0
        # This would be calculated from graded submissions
        return 0.0  # Placeholder
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def publish(self) -> None:
        """Publish the assignment."""
        self.status = AssignmentStatus.PUBLISHED.value
        self.published_at = func.now()
    
    def open_for_submissions(self) -> None:
        """Open assignment for submissions."""
        self.status = AssignmentStatus.OPEN.value
        if not self.published_at:
            self.published_at = func.now()
    
    def close_submissions(self) -> None:
        """Close assignment for submissions."""
        self.status = AssignmentStatus.CLOSED.value
    
    def archive(self) -> None:
        """Archive the assignment."""
        self.status = AssignmentStatus.ARCHIVED.value
    
    def reopen(self) -> None:
        """Reopen a closed assignment."""
        self.status = AssignmentStatus.OPEN.value
    
    def increment_submissions(self) -> None:
        """Increment submission count."""
        self.total_submissions += 1
    
    def increment_graded(self) -> None:
        """Increment graded count."""
        self.graded_count += 1
    
    def update_average_score(self, new_score: float) -> None:
        """Update average score."""
        if self.graded_count == 0:
            self.average_score = 0.00
        else:
            total = self.average_score * (self.graded_count - 1)
            self.average_score = (total + new_score) / self.graded_count
    
    def is_file_type_allowed(self, file_type: str) -> bool:
        """Check if file type is allowed."""
        if not self.allowed_file_types:
            return True
        return file_type in self.allowed_file_types
    
    def soft_delete(self) -> None:
        """Soft delete the assignment."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted assignment."""
        self.deleted_at = None
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert assignment to dictionary."""
        data = {
            "id": self.id,
            "course_id": self.course_id,
            "course_title": self.course.title if self.course else None,
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "assignment_type": self.assignment_type,
            "display_type": self.display_type,
            "status": self.status,
            "display_status": self.display_status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "available_until": self.available_until.isoformat() if self.available_until else None,
            "is_overdue": self.is_overdue,
            "is_available": self.is_available,
            "days_until_due": self.days_until_due,
            "hours_until_due": self.hours_until_due,
            "max_score": self.max_score,
            "passing_score": self.passing_score,
            "weight": float(self.weight) if self.weight else 1.0,
            "max_attempts": self.max_attempts,
            "file_required": self.file_required,
            "text_required": self.text_required,
            "allowed_file_types": self.allowed_file_types,
            "total_submissions": self.total_submissions,
            "graded_count": self.graded_count,
            "average_score": float(self.average_score) if self.average_score else 0.0,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "grace_period_minutes": self.grace_period_minutes,
                "max_file_size": self.max_file_size,
                "plagiarism_check_enabled": self.plagiarism_check_enabled,
                "plagiarism_threshold": self.plagiarism_threshold,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing assignment data."""
        data = self.to_dict()
        data.pop("instructions", None)
        data.pop("metadata", None)
        return data
    
    def to_teacher_json(self) -> dict:
        """Teacher-facing assignment data."""
        return self.to_dict(include_sensitive=True)
    
    def to_admin_json(self) -> dict:
        """Admin-facing assignment data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. SUBMISSION MODEL
# ============================================================

class Submission(Base):
    __tablename__ = "assignment_submissions"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # SUBMISSION CONTENT
    # ============================================================
    content = Column(Text, nullable=True)  # Text submission
    file_url = Column(String(500), nullable=True)  # File submission
    file_name = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # ============================================================
    # SUBMISSION STATUS
    # ============================================================
    status = Column(
        String(20),
        default=SubmissionStatus.SUBMITTED.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # SUBMISSION ATTEMPT
    # ============================================================
    attempt_number = Column(Integer, default=1, nullable=False)
    is_late = Column(Boolean, default=False, nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # ============================================================
    # GRADING
    # ============================================================
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Grade status
    grade_status = Column(
        String(20),
        default=GradeStatus.PENDING.value,
        nullable=False
    )
    
    # ============================================================
    # PLAGIARISM CHECK RESULTS
    # ============================================================
    plagiarism_score = Column(Integer, nullable=True)
    plagiarism_report_url = Column(String(500), nullable=True)
    plagiarism_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # REVISION HISTORY
    # ============================================================
    previous_submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="SET NULL"), nullable=True)
    revision_notes = Column(Text, nullable=True)
    
    # ============================================================
    # METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_submissions_assignment_student', 'assignment_id', 'student_id'),
        Index('ix_submissions_assignment_status', 'assignment_id', 'status'),
        Index('ix_submissions_student_status', 'student_id', 'status'),
        Index('ix_submissions_grade_status', 'grade_status'),
        Index('ix_submissions_late', 'is_late'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    assignment = relationship(
        "Assignment",
        back_populates="submissions",
        foreign_keys=[assignment_id]
    )
    
    student = relationship(
        "User",
        back_populates="assignment_submissions",
        foreign_keys=[student_id]
    )
    
    enrollment = relationship(
        "Enrollment",
        back_populates="assignment_submissions",
        foreign_keys=[enrollment_id]
    )
    
    graded_by_user = relationship(
        "User",
        foreign_keys=[graded_by],
        uselist=False
    )
    
    previous_submission = relationship(
        "Submission",
        remote_side=[id],
        foreign_keys=[previous_submission_id],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Submission {self.id}: {self.student_id} - {self.assignment_id}>"
    
    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.assignment.title}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_submitted(self) -> bool:
        """Check if submission is submitted."""
        return self.status == SubmissionStatus.SUBMITTED.value
    
    @property
    def is_graded(self) -> bool:
        """Check if submission is graded."""
        return self.status == SubmissionStatus.GRADED.value
    
    @property
    def is_late_submission(self) -> bool:
        """Check if submission is late."""
        return self.is_late
    
    @property
    def is_draft(self) -> bool:
        """Check if submission is draft."""
        return self.status == SubmissionStatus.DRAFT.value
    
    @property
    def is_resubmitted(self) -> bool:
        """Check if submission is resubmitted."""
        return self.status == SubmissionStatus.RESUBMITTED.value
    
    @property
    def has_passed(self) -> bool:
        """Check if submission passed."""
        if self.score is None:
            return False
        return self.score >= self.assignment.passing_score if self.assignment else False
    
    @property
    def has_failed(self) -> bool:
        """Check if submission failed."""
        if self.score is None:
            return False
        return self.score < self.assignment.passing_score if self.assignment else False
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "draft": "Draft",
            "submitted": "Submitted",
            "graded": "Graded",
            "resubmitted": "Resubmitted",
            "late": "Late",
            "rejected": "Rejected",
            "excused": "Excused",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def display_grade(self) -> str:
        """Get human-readable grade."""
        if self.score is None:
            return "Pending"
        return f"{self.score}/{self.assignment.max_score if self.assignment else 100}"
    
    @property
    def is_pass_fail_display(self) -> str:
        """Get pass/fail display."""
        if self.score is None:
            return "Not Graded"
        return "✅ Passed" if self.has_passed else "❌ Failed"
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def submit(self, content: str = None, file_url: str = None, file_name: str = None) -> None:
        """
        Submit the assignment.
        
        Args:
            content: Text content
            file_url: URL to uploaded file
            file_name: Original file name
        """
        if content:
            self.content = content
        if file_url:
            self.file_url = file_url
        if file_name:
            self.file_name = file_name
        
        self.status = SubmissionStatus.SUBMITTED.value
        self.submitted_at = func.now()
        
        # Check if late
        if self.assignment and self.assignment.due_date:
            if self.submitted_at > self.assignment.due_date:
                self.is_late = True
                if self.status != SubmissionStatus.LATE.value:
                    self.status = SubmissionStatus.LATE.value
    
    def grade(self, score: int, feedback: str = None, graded_by: int = None) -> None:
        """
        Grade the submission.
        
        Args:
            score: Score awarded
            feedback: Optional feedback text
            graded_by: ID of teacher/admin grading
        """
        self.score = score
        if feedback:
            self.feedback = feedback
        if graded_by:
            self.graded_by = graded_by
        
        self.graded_at = func.now()
        self.status = SubmissionStatus.GRADED.value
        
        # Set grade status
        if self.assignment and score >= self.assignment.passing_score:
            self.grade_status = GradeStatus.PASSED.value
        else:
            self.grade_status = GradeStatus.FAILED.value
        
        # Update assignment stats
        if self.assignment:
            self.assignment.increment_graded()
            self.assignment.update_average_score(score)
    
    def resubmit(self, content: str = None, file_url: str = None, file_name: str = None, notes: str = None) -> None:
        """
        Resubmit after feedback.
        
        Args:
            content: New text content
            file_url: New file URL
            file_name: New file name
            notes: Revision notes
        """
        # Save current as previous
        self.previous_submission_id = self.id
        
        if content:
            self.content = content
        if file_url:
            self.file_url = file_url
        if file_name:
            self.file_name = file_name
        if notes:
            self.revision_notes = notes
        
        self.attempt_number += 1
        self.status = SubmissionStatus.RESUBMITTED.value
        self.submitted_at = func.now()
        self.score = None
        self.feedback = None
        self.graded_by = None
        self.graded_at = None
        self.grade_status = GradeStatus.PENDING.value
    
    def reject(self, reason: str = None) -> None:
        """Reject submission for resubmission."""
        self.status = SubmissionStatus.REJECTED.value
        if reason:
            self.feedback = reason
    
    def excuse(self) -> None:
        """Excuse student from assignment."""
        self.status = SubmissionStatus.EXCUSED.value
        self.grade_status = GradeStatus.EXEMPT.value
    
    def save_draft(self, content: str = None, file_url: str = None, file_name: str = None) -> None:
        """Save as draft."""
        if content:
            self.content = content
        if file_url:
            self.file_url = file_url
        if file_name:
            self.file_name = file_name
        self.status = SubmissionStatus.DRAFT.value
    
    def set_plagiarism_result(self, score: int, report_url: str = None) -> None:
        """Set plagiarism check results."""
        self.plagiarism_score = score
        if report_url:
            self.plagiarism_report_url = report_url
        self.plagiarism_checked_at = func.now()
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete(self) -> None:
        """Soft delete the submission."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted submission."""
        self.deleted_at = None
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert submission to dictionary."""
        data = {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "assignment_title": self.assignment.title if self.assignment else None,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "content": self.content,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "display_status": self.display_status,
            "attempt_number": self.attempt_number,
            "is_late": self.is_late,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "score": self.score,
            "display_grade": self.display_grade,
            "feedback": self.feedback,
            "grade_status": self.grade_status,
            "has_passed": self.has_passed,
            "pass_fail_display": self.is_pass_fail_display,
            "graded_by": self.graded_by,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "plagiarism_score": self.plagiarism_score,
                "plagiarism_report_url": self.plagiarism_report_url,
                "plagiarism_checked_at": self.plagiarism_checked_at.isoformat() if self.plagiarism_checked_at else None,
                "previous_submission_id": self.previous_submission_id,
                "revision_notes": self.revision_notes,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing submission data."""
        data = self.to_dict()
        # Remove sensitive fields for student
        data.pop("plagiarism_score", None)
        data.pop("plagiarism_report_url", None)
        return data
    
    def to_teacher_json(self) -> dict:
        """Teacher-facing submission data."""
        return self.to_dict(include_sensitive=True)
    
    def to_admin_json(self) -> dict:
        """Admin-facing submission data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 3. ASSIGNMENT COMMENT (For teacher-student discussion)
# ============================================================

class AssignmentComment(Base):
    """Comments on assignments (teacher-student discussion)."""
    __tablename__ = "assignment_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)  # Teacher-only comment
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    submission = relationship("Submission", foreign_keys=[submission_id])
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('ix_assignment_comments_submission', 'submission_id'),
        Index('ix_assignment_comments_user', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<AssignmentComment {self.id}>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "content": self.content,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# 4. ASSIGNMENT GRADEBOOK (Bulk grading)
# ============================================================

class GradebookEntry(Base):
    """Gradebook entry for tracking student grades across assignments."""
    __tablename__ = "gradebook_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    score = Column(Integer, nullable=True)
    weight = Column(DECIMAL(5, 2), default=1.00, nullable=False)
    grade_status = Column(String(20), default=GradeStatus.PENDING.value, nullable=False)
    
    # Calculate weighted score
    weighted_score = Column(DECIMAL(10, 2), nullable=True)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course", foreign_keys=[course_id])
    assignment = relationship("Assignment", foreign_keys=[assignment_id])
    
    __table_args__ = (
        Index('ix_gradebook_student_course', 'student_id', 'course_id'),
        Index('ix_gradebook_assignment', 'assignment_id'),
    )
    
    def __repr__(self) -> str:
        return f"<GradebookEntry {self.id}: {self.student_id} - {self.assignment_id}>"