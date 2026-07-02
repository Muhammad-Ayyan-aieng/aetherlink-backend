# ============================================================
# AETHER LINK - USER MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # ============================================================
    # PROFILE
    # ============================================================
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # ============================================================
    # ROLE & STATUS
    # ============================================================
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.STUDENT,
        nullable=False
    )
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    # Teacher: Courses they teach
    taught_courses = relationship(
        "Course",
        back_populates="teacher",
        foreign_keys="Course.teacher_id",
        cascade="all, delete-orphan"
    )
    
    # Student: Enrollments
    enrollments = relationship(
        "Enrollment",
        back_populates="student",
        foreign_keys="Enrollment.student_id",
        cascade="all, delete-orphan"
    )
    
    # Admin: Payments they verified
    verified_payments = relationship(
        "Payment",
        back_populates="verified_by_user",
        foreign_keys="Payment.verified_by",
        cascade="all, delete-orphan"
    )
    
    # Student: Payments they made
    payments = relationship(
        "Payment",
        back_populates="student",
        foreign_keys="Payment.student_id",
        cascade="all, delete-orphan"
    )
    
    # Admin: Enrollments they verified
    verified_enrollments = relationship(
        "Enrollment",
        back_populates="verified_by_user",
        foreign_keys="Enrollment.payment_verified_by",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    def __str__(self) -> str:
        return self.full_name or self.email
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    @property
    def is_student(self) -> bool:
        """Check if user is a student."""
        return self.role == UserRole.STUDENT
    
    @property
    def is_teacher(self) -> bool:
        """Check if user is a teacher."""
        return self.role == UserRole.TEACHER
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_deleted(self) -> bool:
        """Check if user is soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Soft delete the user."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted user."""
        self.deleted_at = None
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
    
    def verify(self) -> None:
        """Mark user as verified."""
        self.is_verified = True
    
    def unverify(self) -> None:
        """Mark user as unverified."""
        self.is_verified = False
