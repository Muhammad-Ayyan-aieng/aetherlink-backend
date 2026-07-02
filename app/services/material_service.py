# ============================================================
# AETHER LINK - MATERIAL SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import html

from ..repositories.material_repository import MaterialRepository
from ..repositories.course_repository import CourseRepository
from ..repositories.user_repository import UserRepository
from ..models.user import UserRole
from ..models.course import CourseStatus
from ..schemas.material import MaterialUpload, MaterialUpdate, MaterialTypeEnum


class MaterialService:
    """Service for course material business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.material_repo = MaterialRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)
    
    # ============================================================
    # UPLOAD
    # ============================================================
    
    def upload_material(self, material_data: MaterialUpload, user_id: int) -> Dict[str, Any]:
        """
        Upload a course material.
        
        Args:
            material_data: Material data
            user_id: Uploader ID
            
        Returns:
            Created material
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check if user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if course exists
        course = self.course_repo.get_by_id(material_data.course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Check permission (teacher or admin)
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to upload materials for this course")
        
        # Check if course is archived
        if course.status == CourseStatus.ARCHIVED:
            raise ValueError("Cannot upload materials to an archived course")
        
        # Validate file type
        if material_data.file_type not in [
            MaterialTypeEnum.PDF,
            MaterialTypeEnum.PPTX,
            MaterialTypeEnum.DOC,
            MaterialTypeEnum.DOCX,
            MaterialTypeEnum.LINK
        ]:
            raise ValueError("Invalid file type. Allowed: pdf, pptx, doc, docx, link")
        
        # Validate file or link
        if material_data.file_type == MaterialTypeEnum.LINK:
            if not material_data.link_url:
                raise ValueError("Link URL is required for link type")
            if not material_data.link_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid link URL")
        else:
            if not material_data.file_url:
                raise ValueError("File URL is required for file types")
            if not material_data.file_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid file URL")
        
        # Validate file size (if file)
        if material_data.file_size:
            max_size = 20 * 1024 * 1024  # 20 MB
            if material_data.file_size > max_size:
                raise ValueError(f"File size must be less than {max_size / (1024 * 1024):.0f} MB")
        
        # Sanitize input
        title = html.escape(material_data.title.strip())
        description = html.escape(material_data.description.strip()) if material_data.description else None
        
        if len(title) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        if description and len(description) > 1000:
            raise ValueError("Description must be less than 1000 characters")
        
        # Determine if link
        is_link = material_data.file_type == MaterialTypeEnum.LINK
        
        # Upload material
        material = self.material_repo.create(
            course_id=material_data.course_id,
            title=title,
            description=description,
            file_url=material_data.file_url,
            file_name=material_data.file_name,
            file_type=material_data.file_type.value,
            file_size=material_data.file_size,
            mime_type=material_data.mime_type,
            uploaded_by=user_id,
            is_link=is_link,
            link_url=material_data.link_url,
            is_published=True,
        )
        
        return self._format_material_response(material)
    
    # ============================================================
    # UPDATE
    # ============================================================
    
    def update_material(
        self, 
        material_id: int, 
        update_data: MaterialUpdate, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        Update a material.
        
        Args:
            material_id: Material ID
            update_data: Update data
            user_id: User making update
            
        Returns:
            Updated material
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check material exists
        material = self.material_repo.get_by_id(material_id)
        if not material:
            raise ValueError("Material not found")
        
        # Check permission
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(material.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to update this material")
        
        # Validate updates
        update_dict = {}
        
        if update_data.title is not None:
            title = html.escape(update_data.title.strip())
            if len(title) < 3:
                raise ValueError("Title must be at least 3 characters")
            update_dict["title"] = title
        
        if update_data.description is not None:
            update_dict["description"] = html.escape(update_data.description.strip()) if update_data.description else None
            if update_dict["description"] and len(update_dict["description"]) > 1000:
                raise ValueError("Description must be less than 1000 characters")
        
        if update_data.is_published is not None:
            update_dict["is_published"] = update_data.is_published
        
        if update_data.file_url is not None:
            if update_data.file_url and not update_data.file_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid file URL")
            update_dict["file_url"] = update_data.file_url
        
        if update_data.file_name is not None:
            update_dict["file_name"] = update_data.file_name
        
        if update_data.file_size is not None:
            max_size = 20 * 1024 * 1024  # 20 MB
            if update_data.file_size > max_size:
                raise ValueError(f"File size must be less than {max_size / (1024 * 1024):.0f} MB")
            update_dict["file_size"] = update_data.file_size
        
        if update_data.link_url is not None:
            if update_data.link_url and not update_data.link_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid link URL")
            update_dict["link_url"] = update_data.link_url
        
        # Apply updates
        for key, value in update_dict.items():
            setattr(material, key, value)
        
        self.db.commit()
        self.db.refresh(material)
        
        return self._format_material_response(material)
    
    # ============================================================
    # READ
    # ============================================================
    
    def get_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get material by ID.
        
        Args:
            material_id: Material ID
            user_id: User requesting
            
        Returns:
            Material details
            
        Raises:
            ValueError: If material not found or permission denied
        """
        material = self.material_repo.get_by_id(material_id)
        if not material:
            raise ValueError("Material not found")
        
        # Check if user can view (enrolled student, teacher, or admin)
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if material is published or user is teacher/admin
        if not material.is_published:
            course = self.course_repo.get_by_id(material.course_id)
            if course and course.teacher_id != user_id and user.role != UserRole.ADMIN:
                raise ValueError("Material is not published")
        
        return self._format_material_response(material)
    
    def get_course_materials(
        self, 
        course_id: int, 
        user_id: int,
        published_only: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get materials for a course.
        
        Args:
            course_id: Course ID
            user_id: User requesting
            published_only: Only published materials
            skip: Pagination offset
            limit: Results limit
            
        Returns:
            Materials and total count
        """
        if limit > 100:
            limit = 100
        
        # Check if course exists
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        # Check permission for unpublished materials
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if published_only:
            materials, total = self.material_repo.get_by_course_paginated(course_id, skip, limit)
            materials = [m for m in materials if m.is_published]
            total = len(materials)
            materials = materials[skip:skip + limit]
        else:
            # Check if user can view all (teacher or admin)
            if course.teacher_id != user_id and user.role != UserRole.ADMIN:
                raise ValueError("You don't have permission to view unpublished materials")
            materials, total = self.material_repo.get_by_course_paginated(course_id, skip, limit)
        
        return {
            "materials": [self._format_material_response(m) for m in materials],
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def publish_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Publish a material.
        
        Args:
            material_id: Material ID
            user_id: User making change
            
        Returns:
            Updated material
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        material = self.material_repo.get_by_id_or_fail(material_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(material.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to publish this material")
        
        if material.is_published:
            raise ValueError("Material is already published")
        
        material.is_published = True
        self.db.commit()
        self.db.refresh(material)
        
        return self._format_material_response(material)
    
    def unpublish_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Unpublish a material.
        
        Args:
            material_id: Material ID
            user_id: User making change
            
        Returns:
            Updated material
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        material = self.material_repo.get_by_id_or_fail(material_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(material.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to unpublish this material")
        
        if not material.is_published:
            raise ValueError("Material is already unpublished")
        
        material.is_published = False
        self.db.commit()
        self.db.refresh(material)
        
        return self._format_material_response(material)
    
    # ============================================================
    # DELETE / RESTORE
    # ============================================================
    
    def delete_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Delete a material.
        
        Args:
            material_id: Material ID
            user_id: User making deletion
            
        Returns:
            Success message
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        material = self.material_repo.get_by_id_or_fail(material_id)
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        course = self.course_repo.get_by_id(material.course_id)
        if not course:
            raise ValueError("Course not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to delete this material")
        
        self.material_repo.soft_delete(material_id)
        
        return {"message": "Material deleted successfully"}
    
    # ============================================================
    # SEARCH
    # ============================================================
    
    def search_materials(
        self, 
        query: str,
        user_id: int,
        course_id: Optional[int] = None,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search materials.
        
        Args:
            query: Search query
            user_id: User searching
            course_id: Optional course filter
            file_type: Optional file type filter
            
        Returns:
            List of materials
        """
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        # Check if user can view unpublished materials
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        published_only = user.role not in [UserRole.TEACHER, UserRole.ADMIN]
        
        materials = self.material_repo.search_materials(
            query=query,
            course_id=course_id,
            file_type=file_type,
            published_only=published_only,
        )
        
        return [self._format_material_response(m) for m in materials]
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_material_stats(self, course_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get material statistics for a course.
        
        Args:
            course_id: Course ID
            user_id: User requesting
            
        Returns:
            Material statistics
        """
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if course.teacher_id != user_id and user.role != UserRole.ADMIN:
            raise ValueError("You don't have permission to view statistics for this course")
        
        return self.material_repo.get_course_stats(course_id)
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _format_material_response(self, material: Any) -> Dict[str, Any]:
        """Format material for response."""
        return {
            "id": material.id,
            "course_id": material.course_id,
            "title": material.title,
            "description": material.description,
            "file_type": material.file_type,
            "file_url": material.file_url,
            "file_name": material.file_name,
            "file_size": material.file_size,
            "size_mb": material.size_mb,
            "mime_type": material.mime_type,
            "is_link": material.is_link,
            "link_url": material.link_url,
            "is_published": material.is_published,
            "uploaded_by": material.uploaded_by,
            "uploader_name": material.uploaded_by_user.full_name if material.uploaded_by_user else None,
            "created_at": material.created_at,
            "updated_at": material.updated_at,
        }