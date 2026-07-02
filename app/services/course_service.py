# ============================================================
# AETHER LINK - COURSE SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import html
import re

from ..repositories.course_repository import CourseRepository
from ..repositories.user_repository import UserRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..models.user import User, UserRole
from ..models.course import Course, CourseStatus
from ..schemas.course import CourseCreate, CourseUpdate


class CourseService:
    """Service for course business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
    
    # ============================================================
    # CREATE
    # ============================================================
    
    def create_course(self, course_data: CourseCreate, teacher_id: int) -> Course:
        """
        Create a new course.
        
        Args:
            course_data: Course creation data
            teacher_id: ID of the teacher (must be teacher or admin)
            
        Returns:
            Created course
            
        Raises:
            ValueError: If validation fails
        """
        # Check if teacher exists and is a teacher
        teacher = self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise ValueError("Teacher not found")
        
        if teacher.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise ValueError("User is not a teacher or admin")
        
        # Check slug uniqueness
        if self.course_repo.is_slug_taken(course_data.slug):
            raise ValueError("Slug already exists. Please choose a different slug.")
        
        # Sanitize input
        title = html.escape(course_data.title.strip())
        description = html.escape(course_data.description.strip()) if course_data.description else None
        
        if len(title) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        if description and len(description) > 5000:
            raise ValueError("Description must be less than 5000 characters")
        
        # Validate price
        if course_data.price < 0 or course_data.price > 999999:
            raise ValueError("Price must be between 0 and 999,999")
        
        # Create course
        course = self.course_repo.create(
            title=title,
            slug=course_data.slug.lower(),
            description=description,
            price=course_data.price,
            thumbnail=course_data.thumbnail,
            teacher_id=teacher_id,
            status=course_data.status.value if course_data.status else CourseStatus.DRAFT.value,
            is_featured=course_data.is_featured,
            meta_title=html.escape(course_data.meta_title.strip()) if course_data.meta_title else None,
            meta_description=html.escape(course_data.meta_description.strip()) if course_data.meta_description else None,
            meta_keywords=html.escape(course_data.meta_keywords.strip()) if course_data.meta_keywords else None,
        )
        
        return course
    
    # ============================================================
    # READ
    # ============================================================
    
    def get_course(self, course_id: int) -> Course:
        """
        Get course by ID.
        
        Args:
            course_id: Course ID
            
        Returns:
            Course
            
        Raises:
            ValueError: If course not found
        """
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        return course
    
    def get_course_by_slug(self, slug: str) -> Course:
        """
        Get course by slug.
        
        Args:
            slug: Course slug
            
        Returns:
            Course
            
        Raises:
            ValueError: If course not found
        """
        course = self.course_repo.get_by_slug(slug)
        if not course:
            raise ValueError("Course not found")
        return course
    
    def get_course_with_details(self, course_id: int) -> Course:
        """
        Get course with all details (teacher, sessions, enrollments).
        
        Args:
            course_id: Course ID
            
        Returns:
            Course with relationships
            
        Raises:
            ValueError: If course not found
        """
        course = self.course_repo.get_full_details(course_id)
        if not course:
            raise ValueError("Course not found")
        return course
    
    def get_published_courses(
        self, 
        skip: int = 0, 
        limit: int = 20,
        featured: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get published courses with pagination.
        
        Args:
            skip: Pagination offset
            limit: Results limit
            featured: Filter by featured
            
        Returns:
            Courses and total count
        """
        if limit > 100:
            limit = 100
        
        if featured is not None:
            # If featured filter, use custom query
            courses = self.course_repo.get_featured(limit) if featured else []
            total = len(courses)
        else:
            courses, total = self.course_repo.get_published(skip, limit)
        
        return {
            "courses": courses,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    def get_courses_by_teacher(self, teacher_id: int) -> List[Course]:
        """
        Get all courses for a teacher.
        
        Args:
            teacher_id: Teacher ID
            
        Returns:
            List of courses
            
        Raises:
            ValueError: If teacher not found
        """
        teacher = self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise ValueError("Teacher not found")
        
        return self.course_repo.get_by_teacher(teacher_id)
    
    def get_teacher_courses_paginated(
        self, 
        teacher_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated courses for a teacher.
        
        Args:
            teacher_id: Teacher ID
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Courses and total count
        """
        if limit > 100:
            limit = 100
        
        courses, total = self.course_repo.get_by_teacher_paginated(teacher_id, skip, limit)
        
        return {
            "courses": courses,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    # ============================================================
    # UPDATE
    # ============================================================
    
    def update_course(self, course_id: int, update_data: CourseUpdate, user_id: int) -> Course:
        """
        Update a course.
        
        Args:
            course_id: Course ID
            update_data: Update data
            user_id: User making the update (teacher or admin)
            
        Returns:
            Updated course
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        course = self.course_repo.get_by_id_or_fail(course_id)
        
        # Check permission
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to update this course")
        
        # Check slug uniqueness if changing
        if update_data.slug and update_data.slug != course.slug:
            if self.course_repo.is_slug_taken(update_data.slug, course_id):
                raise ValueError("Slug already exists")
        
        # Sanitize input
        update_dict = {}
        
        if update_data.title is not None:
            update_dict["title"] = html.escape(update_data.title.strip())
            if len(update_dict["title"]) < 3:
                raise ValueError("Title must be at least 3 characters")
        
        if update_data.slug is not None:
            update_dict["slug"] = update_data.slug.lower()
        
        if update_data.description is not None:
            update_dict["description"] = html.escape(update_data.description.strip()) if update_data.description else None
            if update_dict["description"] and len(update_dict["description"]) > 5000:
                raise ValueError("Description must be less than 5000 characters")
        
        if update_data.price is not None:
            if update_data.price < 0 or update_data.price > 999999:
                raise ValueError("Price must be between 0 and 999,999")
            update_dict["price"] = update_data.price
        
        if update_data.thumbnail is not None:
            update_dict["thumbnail"] = update_data.thumbnail
        
        if update_data.status is not None:
            update_dict["status"] = update_data.status.value
        
        if update_data.is_featured is not None:
            update_dict["is_featured"] = update_data.is_featured
        
        if update_data.meta_title is not None:
            update_dict["meta_title"] = html.escape(update_data.meta_title.strip()) if update_data.meta_title else None
        
        if update_data.meta_description is not None:
            update_dict["meta_description"] = html.escape(update_data.meta_description.strip()) if update_data.meta_description else None
        
        if update_data.meta_keywords is not None:
            update_dict["meta_keywords"] = html.escape(update_data.meta_keywords.strip()) if update_data.meta_keywords else None
        
        # Update course
        for key, value in update_dict.items():
            setattr(course, key, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def publish_course(self, course_id: int, user_id: int) -> Course:
        """
        Publish a course.
        
        Args:
            course_id: Course ID
            user_id: User making the change
            
        Returns:
            Updated course
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        course = self.course_repo.get_by_id_or_fail(course_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to publish this course")
        
        if course.status == CourseStatus.PUBLISHED:
            raise ValueError("Course is already published")
        
        # Check if course has at least one session
        sessions = self.session_repo.get_by_course(course_id)
        if not sessions:
            raise ValueError("Cannot publish course without any sessions")
        
        course.status = CourseStatus.PUBLISHED
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def archive_course(self, course_id: int, user_id: int) -> Course:
        """
        Archive a course.
        
        Args:
            course_id: Course ID
            user_id: User making the change
            
        Returns:
            Updated course
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        course = self.course_repo.get_by_id_or_fail(course_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to archive this course")
        
        if course.status == CourseStatus.ARCHIVED:
            raise ValueError("Course is already archived")
        
        # Check if there are active enrollments
        enrollments = self.enrollment_repo.get_active_by_course(course_id)
        if enrollments:
            raise ValueError("Cannot archive course with active enrollments")
        
        course.status = CourseStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def toggle_featured(self, course_id: int, user_id: int) -> Course:
        """
        Toggle course featured status.
        
        Args:
            course_id: Course ID
            user_id: User making the change
            
        Returns:
            Updated course
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        course = self.course_repo.get_by_id_or_fail(course_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to toggle featured status")
        
        course.is_featured = not course.is_featured
        self.db.commit()
        self.db.refresh(course)
        return course
    
    # ============================================================
    # DELETE / RESTORE
    # ============================================================
    
    def delete_course(self, course_id: int, user_id: int) -> Dict[str, Any]:
        """
        Soft delete a course.
        
        Args:
            course_id: Course ID
            user_id: User making the deletion
            
        Returns:
            Success message
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        course = self.course_repo.get_by_id_or_fail(course_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to delete this course")
        
        # Check if course has active enrollments
        enrollments = self.enrollment_repo.get_active_by_course(course_id)
        if enrollments:
            raise ValueError("Cannot delete course with active enrollments. Archive or cancel enrollments first.")
        
        self.course_repo.soft_delete(course_id)
        
        return {"message": "Course deleted successfully"}
    
    def restore_course(self, course_id: int, user_id: int) -> Course:
        """
        Restore a soft-deleted course.
        
        Args:
            course_id: Course ID
            user_id: User making the restore
            
        Returns:
            Restored course
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        course = self.course_repo.get_by_id(course_id, include_deleted=True)
        if not course:
            raise ValueError("Course not found")
        
        if course.deleted_at is None:
            raise ValueError("Course is not deleted")
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to restore this course")
        
        course.deleted_at = None
        self.db.commit()
        self.db.refresh(course)
        return course
    
    # ============================================================
    # SEARCH
    # ============================================================
    
    def search_courses(
        self, 
        query: str,
        status: Optional[str] = None,
        teacher_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Course]:
        """
        Search courses with filters.
        
        Args:
            query: Search query
            status: Filter by status
            teacher_id: Filter by teacher
            min_price: Minimum price
            max_price: Maximum price
            
        Returns:
            List of courses
        """
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        status_enum = None
        if status:
            try:
                status_enum = CourseStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}")
        
        return self.course_repo.search_courses(
            query=query,
            status=status_enum,
            teacher_id=teacher_id,
            min_price=min_price,
            max_price=max_price,
        )
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_course_stats(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Get course statistics (admin only).
        
        Args:
            admin_user_id: Admin user ID
            
        Returns:
            Course statistics
        """
        user = self.user_repo.get_by_id(admin_user_id)
        if not user or user.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.course_repo.get_stats()
    
    def get_teacher_course_stats(self, teacher_id: int) -> Dict[str, Any]:
        """
        Get course statistics for a teacher.
        
        Args:
            teacher_id: Teacher ID
            
        Returns:
            Teacher course statistics
        """
        teacher = self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise ValueError("Teacher not found")
        
        return self.course_repo.get_teacher_stats(teacher_id)