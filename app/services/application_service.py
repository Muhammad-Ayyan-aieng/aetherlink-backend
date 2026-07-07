# ============================================================
# AETHER LINK - APPLICATION SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from ..repositories.application_repository import ApplicationRepository
from ..repositories.course_repository import CourseRepository
from ..repositories.user_repository import UserRepository
from ..models.application import ApplicationStatus
from ..models.user import UserRole
from ..schemas.application import ApplicationSubmit, ApplicationUpdateStatus
from ..core.security import generate_secure_password, get_password_hash
from .email_service import EmailService

logger = logging.getLogger(__name__)


class ApplicationService:
    """Service for application business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.application_repo = ApplicationRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)
        self.email_service = EmailService()

    # ============================================================
    # SUBMIT APPLICATION (Public)
    # ============================================================

    def submit_application(self, data: ApplicationSubmit) -> Dict[str, Any]:
        """
        Submit a new application.
        
        Args:
            data: Application data
            
        Returns:
            Created application
            
        Raises:
            ValueError: If validation fails
        """
        # Check if course exists
        course = self.course_repo.get_by_id(data.course_id)
        if not course:
            raise ValueError("Course not found")

        # Check if course is published
        if course.status != "published":
            raise ValueError("Course is not accepting applications")

        # Check if email already applied for this course
        existing = self.application_repo.get_by_email_and_course(data.email, data.course_id)
        if existing:
            if existing.status == ApplicationStatus.PENDING:
                raise ValueError("You already have a pending application for this course")
            elif existing.status == ApplicationStatus.APPROVED:
                raise ValueError("You have already been approved for this course")
            elif existing.status == ApplicationStatus.REJECTED:
                raise ValueError("Your previous application was rejected. Please contact support.")

        # Create application
        application = self.application_repo.create(
            email=data.email.lower().strip(),
            full_name=data.full_name.strip(),
            phone=data.phone,
            course_id=data.course_id,
            message=data.message,
            status=ApplicationStatus.PENDING,
        )

        # Send confirmation email to student (async but we don't wait)
        try:
            import asyncio
            asyncio.create_task(
                self.email_service.send_application_confirmation(
                    email=data.email,
                    full_name=data.full_name,
                    course_title=course.title
                )
            )
            logger.info(f"📧 Confirmation email scheduled for {data.email}")
        except Exception as e:
            logger.error(f"❌ Failed to send confirmation email: {e}")

        return self._format_application_response(application)

    # ============================================================
    # GET APPLICATIONS (Student)
    # ============================================================

    def get_student_applications(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all applications for a student.
        
        Args:
            email: Student email
            
        Returns:
            List of applications
        """
        applications = self.application_repo.get_by_email(email)
        return [self._format_application_response(a) for a in applications]

    # ============================================================
    # GET APPLICATIONS (Admin)
    # ============================================================

    def get_all_applications(
        self,
        admin_id: int,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get all applications (admin only).
        
        Args:
            admin_id: Admin ID (for permission check)
            status: Filter by status
            search: Search by email or name
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Paginated applications
            
        Raises:
            ValueError: If permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")

        applications, total = self.application_repo.get_paginated(
            skip=skip,
            limit=limit,
            status=status,
            search=search
        )

        return {
            "applications": [self._format_application_response(a) for a in applications],
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }

    def get_application(self, application_id: int, admin_id: int) -> Dict[str, Any]:
        """
        Get application details (admin only).
        
        Args:
            application_id: Application ID
            admin_id: Admin ID
            
        Returns:
            Application details
            
        Raises:
            ValueError: If permission denied or application not found
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")

        application = self.application_repo.get_with_details(application_id)
        if not application:
            raise ValueError("Application not found")

        return self._format_application_response(application)

    # ============================================================
    # APPROVE/REJECT APPLICATION (Admin)
    # ============================================================

    def approve_application(self, application_id: int, admin_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve an application and create user account.
        
        Args:
            application_id: Application ID
            admin_id: Admin ID
            notes: Admin notes
            
        Returns:
            Approved application with user details
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")

        # Get application
        application = self.application_repo.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != ApplicationStatus.PENDING:
            raise ValueError(f"Application is already {application.status}")

        # Get course for email
        course = self.course_repo.get_by_id(application.course_id)

        # Check if user already exists
        existing_user = self.user_repo.get_by_email(application.email)
        if existing_user:
            # User exists, just approve application
            application = self.application_repo.approve(application_id, admin_id, notes)
            
            # Send approval email (already has account)
            try:
                import asyncio
                asyncio.create_task(
                    self.email_service.send_application_approved(
                        email=application.email,
                        full_name=application.full_name,
                        course_title=course.title if course else "Course",
                        username=existing_user.username,
                        password="Please use your existing password"
                    )
                )
                logger.info(f"📧 Approval email sent to {application.email}")
            except Exception as e:
                logger.error(f"❌ Failed to send approval email: {e}")
            
            return {
                "application": self._format_application_response(application),
                "user_exists": True,
                "user_id": existing_user.id,
                "message": f"Application approved. User {existing_user.email} already exists.",
            }

        # Create new user account
        password = generate_secure_password(12)
        hashed_password = get_password_hash(password)

        # Generate unique username
        username = application.email.split('@')[0]
        if self.user_repo.is_username_taken(username):
            username = f"{username}_{application.id}"

        user = self.user_repo.create(
            email=application.email,
            username=username,
            hashed_password=hashed_password,
            full_name=application.full_name,
            phone=application.phone,
            role=UserRole.STUDENT,
            is_verified=False,
            is_active=True,
        )

        # Approve application
        application = self.application_repo.approve(application_id, admin_id, notes)

        # Send approval email with credentials
        try:
            import asyncio
            asyncio.create_task(
                self.email_service.send_application_approved(
                    email=application.email,
                    full_name=application.full_name,
                    course_title=course.title if course else "Course",
                    username=username,
                    password=password
                )
            )
            logger.info(f"📧 Approval email with credentials sent to {application.email}")
        except Exception as e:
            logger.error(f"❌ Failed to send approval email: {e}")

        return {
            "application": self._format_application_response(application),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "password": password,
            },
            "user_created": True,
            "message": "Application approved and user account created.",
        }

    def reject_application(self, application_id: int, admin_id: int, notes: str) -> Dict[str, Any]:
        """
        Reject an application.
        
        Args:
            application_id: Application ID
            admin_id: Admin ID
            notes: Rejection reason
            
        Returns:
            Rejected application
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")

        # Get application
        application = self.application_repo.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != ApplicationStatus.PENDING:
            raise ValueError(f"Application is already {application.status}")

        if not notes or len(notes.strip()) < 3:
            raise ValueError("Rejection reason is required (minimum 3 characters)")

        # Get course for email
        course = self.course_repo.get_by_id(application.course_id)

        # Reject application
        application = self.application_repo.reject(application_id, admin_id, notes)

        # Send rejection email
        try:
            import asyncio
            asyncio.create_task(
                self.email_service.send_application_rejected(
                    email=application.email,
                    full_name=application.full_name,
                    course_title=course.title if course else "Course",
                    reason=notes
                )
            )
            logger.info(f"📧 Rejection email sent to {application.email}")
        except Exception as e:
            logger.error(f"❌ Failed to send rejection email: {e}")

        return {
            "application": self._format_application_response(application),
            "message": "Application rejected.",
        }

    # ============================================================
    # STATISTICS (Admin)
    # ============================================================

    def get_application_stats(self, admin_id: int) -> Dict[str, Any]:
        """
        Get application statistics (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Application statistics
            
        Raises:
            ValueError: If permission denied
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")

        stats = self.application_repo.get_stats()
        stats["recent_applications"] = [
            self._format_application_response(a)
            for a in stats.get("recent_applications", [])
        ]
        return stats

    # ============================================================
    # HELPERS
    # ============================================================

    def _format_application_response(self, application) -> Dict[str, Any]:
        """Format application for API response."""
        return {
            "id": application.id,
            "email": application.email,
            "full_name": application.full_name,
            "phone": application.phone,
            "course_id": application.course_id,
            "course_title": application.course.title if application.course else None,
            "message": application.message,
            "status": application.status.value,
            "admin_notes": application.admin_notes,
            "approved_by": application.approved_by,
            "approved_at": application.approved_at,
            "rejected_at": application.rejected_at,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
        }