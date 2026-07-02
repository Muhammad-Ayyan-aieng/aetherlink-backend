# ============================================================
# AETHER LINK - USER REPOSITORY
# ============================================================

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional, List, Tuple
from datetime import datetime

from .base import BaseRepository
from ..models.user import User, UserRole
from ..models.course import Course


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(
            User.email == email.lower(),
            User.deleted_at.is_(None)
        ).first()
    
    def get_by_email_or_fail(self, email: str) -> User:
        """Get user by email or raise ValueError."""
        user = self.get_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")
        return user
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(
            User.username == username.lower(),
            User.deleted_at.is_(None)
        ).first()
    
    def get_by_username_or_fail(self, username: str) -> User:
        """Get user by username or raise ValueError."""
        user = self.get_by_username(username)
        if not user:
            raise ValueError(f"User with username {username} not found")
        return user
    
    def get_by_role(self, role: UserRole) -> List[User]:
        """Get all users by role."""
        return self.db.query(User).filter(
            User.role == role,
            User.deleted_at.is_(None)
        ).all()
    
    # ============================================================
    # ROLE-BASED QUERIES
    # ============================================================
    
    def get_teachers(self, active_only: bool = True) -> List[User]:
        """Get all teachers."""
        query = self.db.query(User).filter(
            User.role == UserRole.TEACHER,
            User.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    def get_students(self, active_only: bool = True) -> List[User]:
        """Get all students."""
        query = self.db.query(User).filter(
            User.role == UserRole.STUDENT,
            User.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    def get_admins(self, active_only: bool = True) -> List[User]:
        """Get all admins."""
        query = self.db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return self.db.query(User).filter(
            User.is_active == True,
            User.deleted_at.is_(None)
        ).all()
    
    def get_inactive_users(self) -> List[User]:
        """Get all inactive users."""
        return self.db.query(User).filter(
            User.is_active == False,
            User.deleted_at.is_(None)
        ).all()
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def activate_user(self, user_id: int) -> User:
        """Activate a user account."""
        user = self.get_by_id_or_fail(user_id)
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account."""
        user = self.get_by_id_or_fail(user_id)
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user(self, user_id: int) -> User:
        """Mark user as verified."""
        user = self.get_by_id_or_fail(user_id)
        user.is_verified = True
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user_id: int) -> User:
        """Update user's last login timestamp."""
        user = self.get_by_id_or_fail(user_id)
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ============================================================
    # SEARCH OPERATIONS
    # ============================================================
    
    def search_users(
        self, 
        query: str,
        role: Optional[UserRole] = None,
        active_only: bool = True
    ) -> List[User]:
        """
        Search users by name or email.
        
        Args:
            query: Search query
            role: Filter by role
            active_only: Only active users
            
        Returns:
            List of matching users
        """
        search = f"%{query}%"
        db_query = self.db.query(User).filter(
            or_(
                User.full_name.ilike(search),
                User.email.ilike(search)
            ),
            User.deleted_at.is_(None)
        )
        
        if role:
            db_query = db_query.filter(User.role == role)
        
        if active_only:
            db_query = db_query.filter(User.is_active == True)
        
        return db_query.limit(50).all()
    
    # ============================================================
    # VALIDATION OPERATIONS
    # ============================================================
    
    def is_email_taken(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email is already taken."""
        query = self.db.query(User).filter(
            User.email == email.lower(),
            User.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None
    
    def is_username_taken(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username is already taken."""
        query = self.db.query(User).filter(
            User.username == username.lower(),
            User.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None
    
    # ============================================================
    # COUNT OPERATIONS
    # ============================================================
    
    def count_by_role(self, role: UserRole) -> int:
        """Count users by role."""
        return self.db.query(User).filter(
            User.role == role,
            User.deleted_at.is_(None)
        ).count()
    
    def count_active(self) -> int:
        """Count active users."""
        return self.db.query(User).filter(
            User.is_active == True,
            User.deleted_at.is_(None)
        ).count()
    
    def count_total(self) -> int:
        """Count total users."""
        return self.db.query(User).filter(
            User.deleted_at.is_(None)
        ).count()
    
    def get_stats(self) -> dict:
        """Get user statistics."""
        total = self.count_total()
        active = self.count_active()
        inactive = total - active
        
        teachers = self.count_by_role(UserRole.TEACHER)
        students = self.count_by_role(UserRole.STUDENT)
        admins = self.count_by_role(UserRole.ADMIN)
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "teachers": teachers,
            "students": students,
            "admins": admins,
        }
    
    # ============================================================
    # RELATIONSHIP OPERATIONS
    # ============================================================
    
    def get_with_enrollments(self, user_id: int) -> Optional[User]:
        """Get user with their enrollments loaded."""
        return self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).options(
            # Using selectinload for relationships
            # This will be implemented in the service layer
        ).first()
    
    def get_teacher_with_courses(self, teacher_id: int) -> Optional[User]:
        """Get teacher with their courses loaded."""
        return self.db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER,
            User.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # BULK OPERATIONS
    # ============================================================
    
    def bulk_activate(self, user_ids: List[int]) -> int:
        """Activate multiple users."""
        count = 0
        for user_id in user_ids:
            try:
                self.activate_user(user_id)
                count += 1
            except ValueError:
                continue
        return count
    
    def bulk_deactivate(self, user_ids: List[int]) -> int:
        """Deactivate multiple users."""
        count = 0
        for user_id in user_ids:
            try:
                self.deactivate_user(user_id)
                count += 1
            except ValueError:
                continue
        return count
    
    def bulk_delete(self, user_ids: List[int]) -> int:
        """Soft delete multiple users."""
        count = 0
        for user_id in user_ids:
            try:
                self.soft_delete(user_id)
                count += 1
            except ValueError:
                continue
        return count