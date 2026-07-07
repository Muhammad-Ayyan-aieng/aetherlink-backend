# ============================================================
# AETHER LINK - APPLICATION MODEL
# ============================================================

from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class ApplicationStatus(str, enum.Enum):
    """Application status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Application(Base):
    __tablename__ = "applications"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)

    # ============================================================
    # APPLICANT INFORMATION
    # ============================================================
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)

    # ============================================================
    # COURSE
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    # ============================================================
    # APPLICATION DETAILS
    # ============================================================
    message = Column(Text, nullable=True)
    status = Column(
        SQLEnum(ApplicationStatus, values_callable=lambda x: [e.value for e in x]),
        default=ApplicationStatus.PENDING,
        nullable=False
    )
    admin_notes = Column(Text, nullable=True)

    # ============================================================
    # APPROVAL/REJECTION
    # ============================================================
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship("Course", foreign_keys=[course_id])
    approver = relationship("User", foreign_keys=[approved_by])

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        return f"<Application {self.email} - {self.status}>"

    def __str__(self) -> str:
        return f"{self.full_name} - {self.email}"

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def is_pending(self) -> bool:
        """Check if application is pending."""
        return self.status == ApplicationStatus.PENDING

    def is_approved(self) -> bool:
        """Check if application is approved."""
        return self.status == ApplicationStatus.APPROVED

    def is_rejected(self) -> bool:
        """Check if application is rejected."""
        return self.status == ApplicationStatus.REJECTED

    def approve(self, admin_id: int, notes: Optional[str] = None) -> None:
        """Approve the application."""
        self.status = ApplicationStatus.APPROVED
        self.approved_by = admin_id
        self.approved_at = func.now()
        if notes:
            self.admin_notes = notes

    def reject(self, admin_id: int, notes: str) -> None:
        """Reject the application."""
        self.status = ApplicationStatus.REJECTED
        self.rejected_at = func.now()
        self.admin_notes = notes