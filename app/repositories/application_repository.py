# ============================================================
# AETHER LINK - APPLICATION REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone

from .base import BaseRepository
from ..models.application import Application, ApplicationStatus
from ..models.course import Course
from ..models.user import User


class ApplicationRepository(BaseRepository[Application]):
    """Repository for Application model operations."""

    def __init__(self, db: Session):
        super().__init__(db, Application)

    # Override get_by_id to remove deleted_at filter
    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Application]:
        """Get application by ID without deleted_at filter."""
        return self.db.query(Application).filter(Application.id == id).first()

    def get_by_id_or_fail(self, id: int, include_deleted: bool = False) -> Application:
        """Get application by ID or raise ValueError."""
        application = self.get_by_id(id)
        if not application:
            raise ValueError(f"Application with ID {id} not found")
        return application

    # Override create to handle missing deleted_at
    def create(self, **kwargs) -> Application:
        """Create a new application."""
        application = Application(**kwargs)
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    # Override soft_delete to do nothing (or implement later)
    def soft_delete(self, id: int) -> bool:
        """Soft delete not implemented for applications."""
        raise NotImplementedError("Soft delete not supported for applications")

    # Override restore
    def restore(self, id: int) -> Application:
        """Restore not implemented for applications."""
        raise NotImplementedError("Restore not supported for applications")

    # Override get_all to remove deleted_at filter
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> Tuple[List[Application], int]:
        """Get all applications without deleted_at filter."""
        query = self.db.query(Application)
        
        if order_by and hasattr(Application, order_by):
            column = getattr(Application, order_by)
            query = query.order_by(column.desc() if order_desc else column.asc())
        else:
            query = query.order_by(Application.created_at.desc())
        
        total = query.count()
        records = query.offset(skip).limit(limit).all()
        return records, total

    # ============================================================
    # FIND OPERATIONS
    # ============================================================

    def get_by_email(self, email: str) -> List[Application]:
        """Get all applications for a student email."""
        return self.db.query(Application).filter(
            Application.email == email.lower().strip()
        ).order_by(Application.created_at.desc()).all()

    def get_by_course(self, course_id: int) -> List[Application]:
        """Get all applications for a course."""
        return self.db.query(Application).filter(
            Application.course_id == course_id
        ).order_by(Application.created_at.desc()).all()

    def get_by_email_and_course(self, email: str, course_id: int) -> Optional[Application]:
        """Get application by email and course."""
        return self.db.query(Application).filter(
            Application.email == email.lower().strip(),
            Application.course_id == course_id
        ).first()

    def get_by_status(self, status: ApplicationStatus) -> List[Application]:
        """Get applications by status."""
        return self.db.query(Application).filter(
            Application.status == status
        ).order_by(Application.created_at.desc()).all()

    def get_pending(self) -> List[Application]:
        """Get all pending applications."""
        return self.get_by_status(ApplicationStatus.PENDING)

    def get_pending_with_details(self) -> List[Application]:
        """Get pending applications with course and approver loaded."""
        return self.db.query(Application).options(
            joinedload(Application.course),
            joinedload(Application.approver)
        ).filter(
            Application.status == ApplicationStatus.PENDING
        ).order_by(Application.created_at.asc()).all()

    def get_with_details(self, application_id: int) -> Optional[Application]:
        """Get application with course and approver loaded."""
        return self.db.query(Application).options(
            joinedload(Application.course),
            joinedload(Application.approver)
        ).filter(
            Application.id == application_id
        ).first()

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Application], int]:
        """Get paginated applications with filters."""
        query = self.db.query(Application).options(
            joinedload(Application.course)
        )

        # Apply status filter
        if status:
            try:
                status_enum = ApplicationStatus(status)
                query = query.filter(Application.status == status_enum)
            except ValueError:
                pass

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Application.email.ilike(search_term),
                    Application.full_name.ilike(search_term)
                )
            )

        query = query.order_by(Application.created_at.desc())
        total = query.count()
        applications = query.offset(skip).limit(limit).all()

        return applications, total

    # ============================================================
    # STATUS OPERATIONS
    # ============================================================

    def update_status(
        self,
        application_id: int,
        status: ApplicationStatus,
        admin_id: int,
        notes: Optional[str] = None
    ) -> Application:
        """Update application status."""
        application = self.get_by_id_or_fail(application_id)
        application.status = status
        application.approved_by = admin_id
        application.admin_notes = notes or application.admin_notes

        if status == ApplicationStatus.APPROVED:
            application.approved_at = datetime.now(timezone.utc)
        elif status == ApplicationStatus.REJECTED:
            application.rejected_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(application)
        return application

    def approve(self, application_id: int, admin_id: int, notes: Optional[str] = None) -> Application:
        """Approve an application."""
        return self.update_status(application_id, ApplicationStatus.APPROVED, admin_id, notes)

    def reject(self, application_id: int, admin_id: int, notes: str) -> Application:
        """Reject an application."""
        return self.update_status(application_id, ApplicationStatus.REJECTED, admin_id, notes)

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get application statistics."""
        total = self.db.query(Application).count()
        pending = self.db.query(Application).filter(
            Application.status == ApplicationStatus.PENDING
        ).count()
        approved = self.db.query(Application).filter(
            Application.status == ApplicationStatus.APPROVED
        ).count()
        rejected = self.db.query(Application).filter(
            Application.status == ApplicationStatus.REJECTED
        ).count()

        # Get recent applications
        recent = self.db.query(Application).options(
            joinedload(Application.course)
        ).order_by(Application.created_at.desc()).limit(5).all()

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "recent_applications": recent,
        }

    def count_by_course(self, course_id: int) -> Dict[str, int]:
        """Get application counts by course."""
        total = self.db.query(Application).filter(
            Application.course_id == course_id
        ).count()
        pending = self.db.query(Application).filter(
            Application.course_id == course_id,
            Application.status == ApplicationStatus.PENDING
        ).count()
        approved = self.db.query(Application).filter(
            Application.course_id == course_id,
            Application.status == ApplicationStatus.APPROVED
        ).count()
        rejected = self.db.query(Application).filter(
            Application.course_id == course_id,
            Application.status == ApplicationStatus.REJECTED
        ).count()

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        }