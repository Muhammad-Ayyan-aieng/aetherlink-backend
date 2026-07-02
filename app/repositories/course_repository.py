# ============================================================
# AETHER LINK - COURSE REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import Optional, List, Tuple
from datetime import datetime

from .base import BaseRepository
from ..models.course import Course, CourseStatus
from ..models.user import User, UserRole
from ..models.sessions import Session


class CourseRepository(BaseRepository[Course]):
    """Repository for Course model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Course)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_slug(self, slug: str, include_deleted: bool = False) -> Optional[Course]:
        """Get course by slug."""
        query = self.db.query(Course).filter(Course.slug == slug.lower())
        if not include_deleted:
            query = query.filter(Course.deleted_at.is_(None))
        return query.first()
    
    def get_by_slug_or_fail(self, slug: str) -> Course:
        """Get course by slug or raise ValueError."""
        course = self.get_by_slug(slug)
        if not course:
            raise ValueError(f"Course with slug {slug} not found")
        return course
    
    def get_by_teacher(self, teacher_id: int) -> List[Course]:
        """Get all courses for a teacher."""
        return self.db.query(Course).filter(
            Course.teacher_id == teacher_id,
            Course.deleted_at.is_(None)
        ).all()
    
    def get_by_teacher_paginated(
        self, 
        teacher_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Course], int]:
        """Get paginated courses for a teacher."""
        query = self.db.query(Course).filter(
            Course.teacher_id == teacher_id,
            Course.deleted_at.is_(None)
        )
        total = query.count()
        courses = query.offset(skip).limit(limit).all()
        return courses, total
    
    # ============================================================
    # STATUS-BASED QUERIES
    # ============================================================
    
    def get_published(self, skip: int = 0, limit: int = 20) -> Tuple[List[Course], int]:
        """Get published courses with pagination."""
        query = self.db.query(Course).filter(
            Course.status == CourseStatus.PUBLISHED,
            Course.deleted_at.is_(None)
        ).order_by(Course.created_at.desc())
        total = query.count()
        courses = query.offset(skip).limit(limit).all()
        return courses, total
    
    def get_featured(self, limit: int = 6) -> List[Course]:
        """Get featured courses."""
        return self.db.query(Course).filter(
            Course.status == CourseStatus.PUBLISHED,
            Course.is_featured == True,
            Course.deleted_at.is_(None)
        ).order_by(Course.created_at.desc()).limit(limit).all()
    
    def get_by_status(self, status: CourseStatus) -> List[Course]:
        """Get courses by status."""
        return self.db.query(Course).filter(
            Course.status == status,
            Course.deleted_at.is_(None)
        ).all()
    
    def get_drafts(self) -> List[Course]:
        """Get draft courses."""
        return self.get_by_status(CourseStatus.DRAFT)
    
    def get_archived(self) -> List[Course]:
        """Get archived courses."""
        return self.get_by_status(CourseStatus.ARCHIVED)
    
    def get_active_courses(self) -> List[Course]:
        """Get non-deleted courses."""
        return self.db.query(Course).filter(
            Course.deleted_at.is_(None)
        ).all()
    
    # ============================================================
    # RELATIONSHIP QUERIES (Eager Loading)
    # ============================================================
    
    def get_with_teacher(self, course_id: int) -> Optional[Course]:
        """Get course with teacher loaded."""
        return self.db.query(Course).options(
            joinedload(Course.teacher)
        ).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()
    
    def get_with_sessions(self, course_id: int) -> Optional[Course]:
        """Get course with sessions loaded."""
        return self.db.query(Course).options(
            joinedload(Course.sessions)
        ).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()
    
    def get_with_enrollments(self, course_id: int) -> Optional[Course]:
        """Get course with enrollments loaded."""
        return self.db.query(Course).options(
            joinedload(Course.enrollments)
        ).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()
    
    def get_full_details(self, course_id: int) -> Optional[Course]:
        """Get course with all relationships loaded."""
        return self.db.query(Course).options(
            joinedload(Course.teacher),
            joinedload(Course.sessions),
            joinedload(Course.enrollments)
        ).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # SEARCH OPERATIONS
    # ============================================================
    
    def search_courses(
        self, 
        query: str,
        status: Optional[CourseStatus] = None,
        teacher_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Course]:
        """Search courses with advanced filters."""
        search = f"%{query}%"
        db_query = self.db.query(Course).filter(
            Course.deleted_at.is_(None)
        )
        
        # Search filter
        if query:
            db_query = db_query.filter(
                or_(
                    Course.title.ilike(search),
                    Course.description.ilike(search)
                )
            )
        
        # Status filter
        if status:
            db_query = db_query.filter(Course.status == status)
        else:
            # Default to published if no status specified
            db_query = db_query.filter(Course.status == CourseStatus.PUBLISHED)
        
        # Teacher filter
        if teacher_id:
            db_query = db_query.filter(Course.teacher_id == teacher_id)
        
        # Price filters
        if min_price is not None:
            db_query = db_query.filter(Course.price >= min_price)
        if max_price is not None:
            db_query = db_query.filter(Course.price <= max_price)
        
        return db_query.order_by(Course.created_at.desc()).limit(50).all()
    
    def search_by_title(self, title: str) -> List[Course]:
        """Search courses by title only."""
        search = f"%{title}%"
        return self.db.query(Course).filter(
            Course.title.ilike(search),
            Course.deleted_at.is_(None)
        ).limit(50).all()
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def publish_course(self, course_id: int) -> Course:
        """Publish a course."""
        course = self.get_by_id_or_fail(course_id)
        course.status = CourseStatus.PUBLISHED
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def archive_course(self, course_id: int) -> Course:
        """Archive a course."""
        course = self.get_by_id_or_fail(course_id)
        course.status = CourseStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def draft_course(self, course_id: int) -> Course:
        """Move course to draft."""
        course = self.get_by_id_or_fail(course_id)
        course.status = CourseStatus.DRAFT
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def toggle_featured(self, course_id: int) -> Course:
        """Toggle featured status."""
        course = self.get_by_id_or_fail(course_id)
        course.is_featured = not course.is_featured
        self.db.commit()
        self.db.refresh(course)
        return course
    
    # ============================================================
    # VALIDATION OPERATIONS
    # ============================================================
    
    def is_slug_taken(self, slug: str, exclude_id: Optional[int] = None) -> bool:
        """Check if slug is already taken."""
        query = self.db.query(Course).filter(
            Course.slug == slug.lower(),
            Course.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.filter(Course.id != exclude_id)
        return query.first() is not None
    
    def is_teacher_assigned(self, teacher_id: int) -> bool:
        """Check if teacher has any courses."""
        return self.db.query(Course).filter(
            Course.teacher_id == teacher_id,
            Course.deleted_at.is_(None)
        ).first() is not None
    
    # ============================================================
    # COUNT OPERATIONS
    # ============================================================
    
    def count_by_teacher(self, teacher_id: int) -> int:
        """Count courses for a teacher."""
        return self.db.query(Course).filter(
            Course.teacher_id == teacher_id,
            Course.deleted_at.is_(None)
        ).count()
    
    def count_by_status(self, status: CourseStatus) -> int:
        """Count courses by status."""
        return self.db.query(Course).filter(
            Course.status == status,
            Course.deleted_at.is_(None)
        ).count()
    
    def count_published(self) -> int:
        """Count published courses."""
        return self.count_by_status(CourseStatus.PUBLISHED)
    
    def count_drafts(self) -> int:
        """Count draft courses."""
        return self.count_by_status(CourseStatus.DRAFT)
    
    def count_archived(self) -> int:
        """Count archived courses."""
        return self.count_by_status(CourseStatus.ARCHIVED)
    
    def get_stats(self) -> dict:
        """Get course statistics."""
        total = self.db.query(Course).filter(Course.deleted_at.is_(None)).count()
        published = self.count_by_status(CourseStatus.PUBLISHED)
        drafts = self.count_by_status(CourseStatus.DRAFT)
        archived = self.count_by_status(CourseStatus.ARCHIVED)
        featured = self.db.query(Course).filter(
            Course.is_featured == True,
            Course.deleted_at.is_(None)
        ).count()
        
        return {
            "total": total,
            "published": published,
            "drafts": drafts,
            "archived": archived,
            "featured": featured,
            "free": self.db.query(Course).filter(Course.price == 0, Course.deleted_at.is_(None)).count(),
        }
    
    # ============================================================
    # BULK OPERATIONS
    # ============================================================
    
    def bulk_update_status(self, course_ids: List[int], status: CourseStatus) -> int:
        """Update status for multiple courses."""
        count = 0
        for course_id in course_ids:
            try:
                course = self.get_by_id(course_id)
                if course:
                    course.status = status
                    count += 1
            except Exception:
                continue
        self.db.commit()
        return count
    
    def bulk_delete(self, course_ids: List[int]) -> int:
        """Soft delete multiple courses."""
        count = 0
        for course_id in course_ids:
            try:
                self.soft_delete(course_id)
                count += 1
            except ValueError:
                continue
        return count
    
    # ============================================================
    # TEACHER VALIDATION
    # ============================================================
    
    def get_teacher_stats(self, teacher_id: int) -> dict:
        """Get statistics for a teacher."""
        total_courses = self.count_by_teacher(teacher_id)
        published = self.db.query(Course).filter(
            Course.teacher_id == teacher_id,
            Course.status == CourseStatus.PUBLISHED,
            Course.deleted_at.is_(None)
        ).count()
        
        students = self.db.query(Course).join(
            Course.enrollments
        ).filter(
            Course.teacher_id == teacher_id,
            Course.deleted_at.is_(None),
            Course.enrollments.has(deleted_at=None)
        ).count()
        
        revenue = self.db.query(func.sum(Course.price)).filter(
            Course.teacher_id == teacher_id,
            Course.status == CourseStatus.PUBLISHED,
            Course.deleted_at.is_(None)
        ).scalar() or 0
        
        return {
            "total_courses": total_courses,
            "published_courses": published,
            "total_students": students,
            "total_revenue": float(revenue),
        }