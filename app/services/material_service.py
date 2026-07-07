# ============================================================
# AETHER LINK - MATERIAL SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import html
import logging
from fastapi import UploadFile

from ..repositories.material_repository import MaterialRepository
from ..repositories.course_repository import CourseRepository
from ..repositories.user_repository import UserRepository
from ..models.user import UserRole
from ..models.course import CourseStatus
from ..models.material import CourseMaterial
from ..schemas.material import MaterialUpload, MaterialUpdate, MaterialTypeEnum
from ..core.config import settings
from ..core.supabase import (
    upload_file_to_storage,
    delete_file_from_storage,
    get_signed_url,
    file_exists
)
from ..utils.sanitizer import sanitize_text

logger = logging.getLogger(__name__)


class MaterialService:
    """Service for course material business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.material_repo = MaterialRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)
    
    # ============================================================
    # UPLOAD (WITH FILE UPLOAD TO SUPABASE)
    # ============================================================
    
    async def upload_material(
        self, 
        material_data: MaterialUpload, 
        file: Optional[UploadFile],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Upload a course material with file to Supabase Storage.
        
        Args:
            material_data: Material data
            file: UploadFile object (for file types)
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
            MaterialTypeEnum.LINK,
            MaterialTypeEnum.TXT
        ]:
            raise ValueError("Invalid file type. Allowed: pdf, pptx, doc, docx, link, txt")
        
        is_link = material_data.file_type == MaterialTypeEnum.LINK
        storage_path = None
        uploaded_file_name = None
        uploaded_file_size = None
        uploaded_mime_type = None
        
        # ============================================================
        # HANDLE LINK TYPE
        # ============================================================
        if is_link:
            if not material_data.link_url:
                raise ValueError("Link URL is required for link type")
            if not material_data.link_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid link URL")
        
        # ============================================================
        # HANDLE FILE TYPE - UPLOAD TO SUPABASE STORAGE
        # ============================================================
        else:
            if not file:
                raise ValueError("File is required for file types")
            
            # Upload to Supabase Storage
            try:
                upload_result = await upload_file_to_storage(
                    file=file,
                    course_id=material_data.course_id,
                    folder="materials"
                )
                storage_path = upload_result["storage_path"]
                uploaded_file_name = upload_result["file_name"]
                uploaded_file_size = upload_result["file_size"]
                uploaded_mime_type = upload_result["mime_type"]
            except Exception as e:
                raise ValueError(f"File upload failed: {str(e)}")
        
        # Sanitize input
        title = sanitize_text(material_data.title.strip(), max_length=255)
        description = sanitize_text(material_data.description.strip(), max_length=1000) if material_data.description else None
        
        if len(title) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        # Create material in database
        try:
            material = self.material_repo.create(
                course_id=material_data.course_id,
                title=title,
                description=description,
                file_url=material_data.file_url or storage_path,
                file_name=material_data.file_name or uploaded_file_name,
                file_type=material_data.file_type.value,
                file_size=material_data.file_size or uploaded_file_size,
                mime_type=material_data.mime_type or uploaded_mime_type,
                uploaded_by=user_id,
                is_link=is_link,
                link_url=material_data.link_url,
                is_published=True,
                storage_path=storage_path,
            )
        except Exception as e:
            # If DB fails, clean up storage
            if storage_path:
                try:
                    delete_file_from_storage(storage_path)
                except Exception:
                    pass
            raise ValueError(f"Failed to save material: {str(e)}")
        
        self.db.commit()
        self.db.refresh(material)
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
            title = sanitize_text(update_data.title.strip(), max_length=255)
            if len(title) < 3:
                raise ValueError("Title must be at least 3 characters")
            update_dict["title"] = title
        
        if update_data.description is not None:
            desc = sanitize_text(update_data.description.strip(), max_length=1000) if update_data.description else None
            update_dict["description"] = desc
        
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
    # READ - WITH SIGNED URL
    # ============================================================
    
    def get_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get material by ID with signed URL for file access.
        
        Args:
            material_id: Material ID
            user_id: User requesting
            
        Returns:
            Material details with signed URL
            
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
        
        response = self._format_material_response(material)
        
        # ============================================================
        # ⭐ GENERATE SIGNED URL
        # ============================================================
        logger.info(f"🔍 Checking signed URL for material {material_id}: storage_path={material.storage_path}, is_link={material.is_link}")
        
        if material.storage_path and not material.is_link:
            try:
                logger.info(f"🔐 Generating signed URL for: {material.storage_path}")
                signed_url = get_signed_url(
                    material.storage_path, 
                    expires_in=settings.SIGNED_URL_EXPIRY
                )
                response["file_url"] = signed_url
                response["signed_url_expiry"] = settings.SIGNED_URL_EXPIRY
                logger.info(f"✅ Signed URL generated successfully")
            except Exception as e:
                logger.error(f"❌ Failed to generate signed URL: {e}")
                response["file_url"] = None
                response["signed_url_error"] = str(e)
        else:
            logger.warning(f"⚠️ Skipping signed URL: storage_path={material.storage_path}, is_link={material.is_link}")
        
        return response
    
    def get_course_materials(
        self, 
        course_id: int, 
        user_id: int,
        published_only: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get materials for a course with signed URLs.
        
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
        
        # Format response with signed URLs
        formatted_materials = []
        for material in materials:
            formatted = self._format_material_response(material)
            
            # Generate signed URL if file exists in storage
            if material.storage_path and not material.is_link:
                try:
                    signed_url = get_signed_url(
                        material.storage_path,
                        expires_in=settings.SIGNED_URL_EXPIRY
                    )
                    formatted["file_url"] = signed_url
                except Exception as e:
                    logger.error(f"Failed to generate signed URL: {e}")
                    formatted["file_url"] = None
            
            formatted_materials.append(formatted)
        
        return {
            "materials": formatted_materials,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    # ============================================================
    # PUBLIC METHODS (No Auth)
    # ============================================================
    
    def get_course_materials_public(
        self, 
        course_id: int,
        published_only: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Public access - only published materials."""
        materials, total = self.material_repo.get_by_course_paginated(course_id, skip, limit)
        materials = [m for m in materials if m.is_published]
        total = len(materials)
        materials = materials[skip:skip + limit]
        
        formatted_materials = []
        for material in materials:
            formatted = self._format_material_response(material)
            # For public access, only show file_url if it's a link
            if material.is_link:
                formatted["file_url"] = material.link_url
            else:
                formatted["file_url"] = None
            formatted_materials.append(formatted)
        
        return {
            "materials": formatted_materials,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    
    def get_material_public(self, material_id: int) -> Dict[str, Any]:
        """Public access - only published materials."""
        material = self.material_repo.get_by_id(material_id)
        if not material:
            raise ValueError("Material not found")
        
        if not material.is_published:
            raise ValueError("Material not published")
        
        response = self._format_material_response(material)
        if material.is_link:
            response["file_url"] = material.link_url
        else:
            response["file_url"] = None
        
        return response
    
    def search_materials_public(
        self, 
        query: str,
        course_id: Optional[int] = None,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Public search - only published materials."""
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        materials = self.material_repo.search_materials(
            query=query,
            course_id=course_id,
            file_type=file_type,
            published_only=True,
        )
        
        formatted = []
        for material in materials:
            resp = self._format_material_response(material)
            if material.is_link:
                resp["file_url"] = material.link_url
            else:
                resp["file_url"] = None
            formatted.append(resp)
        
        return formatted
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def publish_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Publish a material.
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
    # DELETE / RESTORE (WITH STORAGE CLEANUP)
    # ============================================================
    
    def delete_material(self, material_id: int, user_id: int) -> Dict[str, Any]:
        """
        Delete a material - removes from storage and database.
        
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
        
        # Delete from storage first
        if material.storage_path and not material.is_link:
            try:
                delete_file_from_storage(material.storage_path)
                logger.info(f"Deleted file from storage: {material.storage_path}")
            except Exception as e:
                logger.error(f"Failed to delete file from storage: {e}")
        
        # Soft delete from database
        self.material_repo.soft_delete(material_id)
        
        return {"message": "Material deleted successfully"}
    
    # ============================================================
    # SEARCH (Authenticated)
    # ============================================================
    
    def search_materials(
        self, 
        query: str,
        user_id: int,
        course_id: Optional[int] = None,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search materials with signed URLs.
        """
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
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
        
        formatted = []
        for material in materials:
            resp = self._format_material_response(material)
            
            # Generate signed URL if file exists in storage
            if material.storage_path and not material.is_link:
                try:
                    signed_url = get_signed_url(
                        material.storage_path,
                        expires_in=settings.SIGNED_URL_EXPIRY
                    )
                    resp["file_url"] = signed_url
                except Exception:
                    resp["file_url"] = None
            
            formatted.append(resp)
        
        return formatted
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_material_stats(self, course_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get material statistics for a course.
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
    
    def _format_material_response(self, material: CourseMaterial) -> Dict[str, Any]:
        """
        Format material for API response.
        """
        # Get uploader name safely
        uploader_name = None
        if hasattr(material, 'uploader') and material.uploader:
            uploader_name = material.uploader.full_name
        elif hasattr(material, 'uploaded_by_user') and material.uploaded_by_user:
            uploader_name = material.uploaded_by_user.full_name
        
        # Calculate size in MB
        size_mb = None
        if material.file_size:
            size_mb = round(material.file_size / (1024 * 1024), 2)
        
        return {
            "id": material.id,
            "course_id": material.course_id,
            "title": material.title,
            "description": material.description,
            "file_type": material.file_type,
            "file_url": material.file_url,
            "file_name": material.file_name,
            "file_size": material.file_size,
            "size_mb": size_mb,
            "mime_type": material.mime_type,
            "is_link": material.is_link,
            "link_url": material.link_url,
            "is_published": material.is_published,
            "uploaded_by": material.uploaded_by,
            "uploader_name": uploader_name,
            "storage_path": material.storage_path,
            "created_at": material.created_at,
            "updated_at": material.updated_at,
        }