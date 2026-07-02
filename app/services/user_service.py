# ============================================================
# AETHER LINK - USER SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import html
import re

from ..repositories.user_repository import UserRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..repositories.course_repository import CourseRepository
from ..models.user import User, UserRole
from ..schemas.user import UserUpdate, UserRoleUpdate


class UserService:
    """Service for user management business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
    
    # ============================================================
    # PROFILE MANAGEMENT
    # ============================================================
    
    def get_user_profile(self, user_id: int) -> User:
        """
        Get user profile by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User
            
        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user
    
    def get_user_profile_by_email(self, email: str) -> User:
        """
        Get user profile by email.
        
        Args:
            email: User email
            
        Returns:
            User
            
        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        return user
    
    def update_profile(self, user_id: int, update_data: UserUpdate) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            update_data: Update data
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If validation fails
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        # Sanitize text fields
        if update_data.full_name is not None:
            update_data.full_name = html.escape(update_data.full_name.strip())
            if len(update_data.full_name) < 1 or len(update_data.full_name) > 100:
                raise ValueError("Full name must be between 1 and 100 characters")
        
        if update_data.bio is not None:
            update_data.bio = html.escape(update_data.bio.strip())
            if len(update_data.bio) > 500:
                raise ValueError("Bio must be less than 500 characters")
        
        if update_data.phone is not None:
            if update_data.phone:
                # Basic phone validation
                cleaned = re.sub(r'[\s\-\(\)]', '', update_data.phone)
                if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
                    raise ValueError("Invalid phone number format")
        
        if update_data.profile_picture is not None:
            if update_data.profile_picture and not update_data.profile_picture.startswith(('http://', 'https://')):
                raise ValueError("Profile picture must be a valid URL")
        
        # Update user
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_profile_picture(self, user_id: int, picture_url: str) -> User:
        """
        Update user profile picture.
        
        Args:
            user_id: User ID
            picture_url: New profile picture URL
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If URL invalid
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if not picture_url.startswith(('http://', 'https://')):
            raise ValueError("Profile picture must be a valid URL")
        
        if len(picture_url) > 500:
            raise ValueError("Profile picture URL too long")
        
        user.profile_picture = picture_url
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ============================================================
    # USER LISTING (Admin)
    # ============================================================
    
    def get_users(
        self, 
        skip: int = 0, 
        limit: int = 20,
        role: Optional[UserRole] = None,
        active_only: bool = True,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get users with filters and pagination.
        
        Args:
            skip: Pagination offset
            limit: Results limit (max 100)
            role: Filter by role
            active_only: Only active users
            search: Search query
            
        Returns:
            Users and total count
        """
        if limit > 100:
            limit = 100
        
        if search:
            users = self.user_repo.search_users(search, role, active_only)
            total = len(users)
        elif role:
            users = self.user_repo.get_by_role(role)
            if active_only:
                users = [u for u in users if u.is_active]
            total = len(users)
            # Apply pagination manually
            users = users[skip:skip + limit]
        else:
            users, total = self.user_repo.get_all(skip=skip, limit=limit)
            if active_only:
                # Filter active users (will be done in repository)
                pass
        
        return {
            "users": users,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    def get_teachers(self, active_only: bool = True) -> List[User]:
        """Get all teachers."""
        return self.user_repo.get_teachers(active_only)
    
    def get_students(self, active_only: bool = True) -> List[User]:
        """Get all students."""
        return self.user_repo.get_students(active_only)
    
    def get_admins(self, active_only: bool = True) -> List[User]:
        """Get all admins."""
        return self.user_repo.get_admins(active_only)
    
    # ============================================================
    # USER STATUS MANAGEMENT (Admin)
    # ============================================================
    
    def activate_user(self, user_id: int) -> User:
        """
        Activate a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Activated user
            
        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if user.is_active:
            raise ValueError("User is already active")
        
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Deactivated user
            
        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if not user.is_active:
            raise ValueError("User is already inactive")
        
        # Prevent deactivating yourself
        # This check should be done in the API layer
        
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user(self, user_id: int) -> User:
        """
        Mark user as verified.
        
        Args:
            user_id: User ID
            
        Returns:
            Verified user
            
        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if user.is_verified:
            raise ValueError("User is already verified")
        
        user.is_verified = True
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ============================================================
    # ROLE MANAGEMENT (Admin)
    # ============================================================
    
    def promote_to_teacher(self, user_id: int) -> User:
        """
        Promote a student to teacher.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If user not found or not a student
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if user.role == UserRole.ADMIN:
            raise ValueError("Cannot promote admin to teacher")
        
        if user.role == UserRole.TEACHER:
            raise ValueError("User is already a teacher")
        
        # Check if user has any active enrollments (as student)
        enrollments = self.enrollment_repo.get_active_by_student(user_id)
        if enrollments:
            raise ValueError("Cannot promote user with active enrollments")
        
        user.role = UserRole.TEACHER
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def demote_to_student(self, user_id: int) -> User:
        """
        Demote a teacher to student.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If user not found or not a teacher
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if user.role == UserRole.ADMIN:
            raise ValueError("Cannot demote admin to student")
        
        if user.role == UserRole.STUDENT:
            raise ValueError("User is already a student")
        
        # Check if teacher has any courses
        courses = self.course_repo.get_by_teacher(user_id)
        if courses:
            raise ValueError("Cannot demote teacher with active courses")
        
        user.role = UserRole.STUDENT
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_role(self, user_id: int, role_data: UserRoleUpdate) -> User:
        """
        Update user role (admin only).
        
        Args:
            user_id: User ID
            role_data: New role
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If validation fails
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        if role_data.role == user.role:
            raise ValueError("User already has this role")
        
        if role_data.role == UserRole.ADMIN:
            # Only super admin can create admins (handled in API layer)
            raise ValueError("Admin role cannot be assigned this way")
        
        if role_data.role == UserRole.TEACHER:
            # Check if student has active enrollments
            if user.role == UserRole.STUDENT:
                enrollments = self.enrollment_repo.get_active_by_student(user_id)
                if enrollments:
                    raise ValueError("Cannot promote student with active enrollments")
        else:
            # Demoting to student - check if teacher has courses
            if user.role == UserRole.TEACHER:
                courses = self.course_repo.get_by_teacher(user_id)
                if courses:
                    raise ValueError("Cannot demote teacher with active courses")
        
        user.role = role_data.role
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ============================================================
    # USER DELETION (Admin)
    # ============================================================
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """
        Soft delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Success message
            
        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        # Prevent deleting yourself (handled in API layer)
        
        # Check if user has active courses (if teacher)
        if user.role == UserRole.TEACHER:
            courses = self.course_repo.get_by_teacher(user_id)
            if courses:
                raise ValueError("Cannot delete teacher with active courses. Archive courses first.")
        
        # Check if user has active enrollments (if student)
        if user.role == UserRole.STUDENT:
            enrollments = self.enrollment_repo.get_active_by_student(user_id)
            if enrollments:
                raise ValueError("Cannot delete student with active enrollments. Cancel enrollments first.")
        
        self.user_repo.soft_delete(user_id)
        
        return {"message": "User deleted successfully"}
    
    def restore_user(self, user_id: int) -> User:
        """
        Restore a soft-deleted user.
        
        Args:
            user_id: User ID
            
        Returns:
            Restored user
            
        Raises:
            ValueError: If user not found or not deleted
        """
        user = self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            raise ValueError("User not found")
        
        if user.deleted_at is None:
            raise ValueError("User is not deleted")
        
        user.deleted_at = None
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ============================================================
    # SEARCH
    # ============================================================
    
    def search_users(self, query: str) -> List[User]:
        """
        Search users by name or email.
        
        Args:
            query: Search query
            
        Returns:
            List of users
        """
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        return self.user_repo.search_users(query)
    
    # ============================================================
    # STATISTICS (Admin)
    # ============================================================
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            User statistics
        """
        return self.user_repo.get_stats()
    
    def get_teacher_stats(self, teacher_id: int) -> Dict[str, Any]:
        """
        Get statistics for a teacher.
        
        Args:
            teacher_id: Teacher ID
            
        Returns:
            Teacher statistics
        """
        teacher = self.user_repo.get_by_id_or_fail(teacher_id)
        
        if teacher.role != UserRole.TEACHER:
            raise ValueError("User is not a teacher")
        
        return self.course_repo.get_teacher_stats(teacher_id)
    
    def get_recent_users(self, limit: int = 10) -> List[User]:
        """
        Get recently registered users.
        
        Args:
            limit: Max users to return
            
        Returns:
            List of recent users
        """
        users, _ = self.user_repo.get_all(
            skip=0, 
            limit=limit, 
            order_by="created_at", 
            order_desc=True
        )
        return users