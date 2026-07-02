# ============================================================
# AETHER LINK - MATERIAL REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from .base import BaseRepository
from ..models.material import CourseMaterial
from ..models.user import User
from ..models.course import Course


class MaterialRepository(BaseRepository[CourseMaterial]):
    """Repository for CourseMaterial model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, CourseMaterial)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_course(self, course_id: int) -> List[CourseMaterial]:
        """Get all materials for a course."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.deleted_at.is_(None)
        ).order_by(CourseMaterial.created_at.desc()).all()
    
    def get_by_course_paginated(
        self, 
        course_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[CourseMaterial], int]:
        """Get paginated materials for a course."""
        query = self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.deleted_at.is_(None)
        ).order_by(CourseMaterial.created_at.desc())
        total = query.count()
        materials = query.offset(skip).limit(limit).all()
        return materials, total
    
    def get_published_by_course(self, course_id: int) -> List[CourseMaterial]:
        """Get only published materials for a course."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.is_published == True,
            CourseMaterial.deleted_at.is_(None)
        ).order_by(CourseMaterial.created_at.desc()).all()
    
    def get_by_uploader(self, uploader_id: int) -> List[CourseMaterial]:
        """Get materials uploaded by a specific user."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.uploaded_by == uploader_id,
            CourseMaterial.deleted_at.is_(None)
        ).order_by(CourseMaterial.created_at.desc()).all()
    
    def get_by_type(self, file_type: str) -> List[CourseMaterial]:
        """Get materials by file type."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.file_type == file_type,
            CourseMaterial.deleted_at.is_(None)
        ).all()
    
    # ============================================================
    # RELATIONSHIP QUERIES
    # ============================================================
    
    def get_with_uploader(self, material_id: int) -> Optional[CourseMaterial]:
        """Get material with uploader loaded."""
        return self.db.query(CourseMaterial).options(
            joinedload(CourseMaterial.uploaded_by_user)
        ).filter(
            CourseMaterial.id == material_id,
            CourseMaterial.deleted_at.is_(None)
        ).first()
    
    def get_with_course(self, material_id: int) -> Optional[CourseMaterial]:
        """Get material with course loaded."""
        return self.db.query(CourseMaterial).options(
            joinedload(CourseMaterial.course)
        ).filter(
            CourseMaterial.id == material_id,
            CourseMaterial.deleted_at.is_(None)
        ).first()
    
    def get_course_materials_with_details(self, course_id: int) -> List[Dict[str, Any]]:
        """Get materials with uploader and course details."""
        materials = self.db.query(CourseMaterial).options(
            joinedload(CourseMaterial.uploaded_by_user),
            joinedload(CourseMaterial.course)
        ).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.deleted_at.is_(None)
        ).order_by(CourseMaterial.created_at.desc()).all()
        
        return [
            {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "file_type": m.file_type,
                "file_url": m.file_url,
                "file_name": m.file_name,
                "file_size": m.file_size,
                "is_link": m.is_link,
                "link_url": m.link_url,
                "is_published": m.is_published,
                "uploaded_by": m.uploaded_by,
                "uploader_name": m.uploaded_by_user.full_name if m.uploaded_by_user else None,
                "course_id": m.course_id,
                "course_title": m.course.title if m.course else None,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
                "size_mb": m.size_mb,
            }
            for m in materials
        ]
    
    # ============================================================
    # STATUS OPERATIONS
    # ============================================================
    
    def publish_material(self, material_id: int) -> CourseMaterial:
        """Publish a material."""
        material = self.get_by_id_or_fail(material_id)
        material.is_published = True
        self.db.commit()
        self.db.refresh(material)
        return material
    
    def unpublish_material(self, material_id: int) -> CourseMaterial:
        """Unpublish a material."""
        material = self.get_by_id_or_fail(material_id)
        material.is_published = False
        self.db.commit()
        self.db.refresh(material)
        return material
    
    # ============================================================
    # COUNT OPERATIONS
    # ============================================================
    
    def count_by_course(self, course_id: int) -> int:
        """Count materials for a course."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.deleted_at.is_(None)
        ).count()
    
    def count_published_by_course(self, course_id: int) -> int:
        """Count published materials for a course."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.is_published == True,
            CourseMaterial.deleted_at.is_(None)
        ).count()
    
    def count_by_type(self, file_type: str) -> int:
        """Count materials by file type."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.file_type == file_type,
            CourseMaterial.deleted_at.is_(None)
        ).count()
    
    def count_by_uploader(self, uploader_id: int) -> int:
        """Count materials uploaded by a user."""
        return self.db.query(CourseMaterial).filter(
            CourseMaterial.uploaded_by == uploader_id,
            CourseMaterial.deleted_at.is_(None)
        ).count()
    
    def get_course_stats(self, course_id: int) -> Dict[str, Any]:
        """Get material statistics for a course."""
        total = self.count_by_course(course_id)
        published = self.count_published_by_course(course_id)
        links = self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.is_link == True,
            CourseMaterial.deleted_at.is_(None)
        ).count()
        files = total - links
        
        return {
            "total": total,
            "published": published,
            "unpublished": total - published,
            "files": files,
            "links": links,
        }
    
    def get_upload_stats(self, uploader_id: int) -> Dict[str, Any]:
        """Get upload statistics for a user."""
        total = self.count_by_uploader(uploader_id)
        published = self.db.query(CourseMaterial).filter(
            CourseMaterial.uploaded_by == uploader_id,
            CourseMaterial.is_published == True,
            CourseMaterial.deleted_at.is_(None)
        ).count()
        
        # Get file type breakdown
        file_types = self.db.query(
            CourseMaterial.file_type,
            func.count(CourseMaterial.id).label('count')
        ).filter(
            CourseMaterial.uploaded_by == uploader_id,
            CourseMaterial.deleted_at.is_(None)
        ).group_by(CourseMaterial.file_type).all()
        
        return {
            "total": total,
            "published": published,
            "unpublished": total - published,
            "file_types": {ft.file_type: ft.count for ft in file_types},
        }
    
    # ============================================================
    # SEARCH OPERATIONS
    # ============================================================
    
    def search_materials(
        self, 
        query: str,
        course_id: Optional[int] = None,
        file_type: Optional[str] = None,
        published_only: bool = True
    ) -> List[CourseMaterial]:
        """Search materials by title or description."""
        search = f"%{query}%"
        db_query = self.db.query(CourseMaterial).filter(
            CourseMaterial.deleted_at.is_(None)
        )
        
        # Search filter
        if query:
            db_query = db_query.filter(
                or_(
                    CourseMaterial.title.ilike(search),
                    CourseMaterial.description.ilike(search)
                )
            )
        
        # Course filter
        if course_id:
            db_query = db_query.filter(CourseMaterial.course_id == course_id)
        
        # File type filter
        if file_type:
            db_query = db_query.filter(CourseMaterial.file_type == file_type)
        
        # Published only
        if published_only:
            db_query = db_query.filter(CourseMaterial.is_published == True)
        
        return db_query.order_by(CourseMaterial.created_at.desc()).limit(50).all()
    
    # ============================================================
    # BULK OPERATIONS
    # ============================================================
    
    def bulk_publish(self, material_ids: List[int]) -> int:
        """Publish multiple materials."""
        count = 0
        for material_id in material_ids:
            try:
                self.publish_material(material_id)
                count += 1
            except ValueError:
                continue
        return count
    
    def bulk_unpublish(self, material_ids: List[int]) -> int:
        """Unpublish multiple materials."""
        count = 0
        for material_id in material_ids:
            try:
                self.unpublish_material(material_id)
                count += 1
            except ValueError:
                continue
        return count
    
    def bulk_delete_by_course(self, course_id: int) -> int:
        """Soft delete all materials for a course."""
        materials = self.db.query(CourseMaterial).filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.deleted_at.is_(None)
        ).all()
        
        count = 0
        for material in materials:
            self.soft_delete(material.id)
            count += 1
        
        return count