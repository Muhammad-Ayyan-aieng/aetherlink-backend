# ============================================================
# AETHER LINK - COURSE MATERIAL MODEL
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # COURSE RELATIONSHIP
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # ============================================================
    # FILE INFORMATION
    # ============================================================
    file_url = Column(String(500), nullable=True)           # Cloud storage URL
    file_name = Column(String(255), nullable=True)          # Original file name
    file_type = Column(String(50), nullable=False)          # pdf, pptx, doc, docx, link
    file_size = Column(Integer, nullable=True)              # Size in bytes
    mime_type = Column(String(100), nullable=True)          # application/pdf, etc.
    
    # ============================================================
    # SUPABASE STORAGE
    # ============================================================
    storage_path = Column(String(500), nullable=True)       # Path in Supabase Storage
    
    # ============================================================
    # LINK INFORMATION
    # ============================================================
    is_link = Column(Boolean, default=False, nullable=False)  # True if it's a link
    link_url = Column(String(500), nullable=True)             # YouTube/Vimeo link
    
    # ============================================================
    # PUBLISHING
    # ============================================================
    is_published = Column(Boolean, default=True, nullable=False)
    
    # ============================================================
    # UPLOADER
    # ============================================================
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_course_materials_course', 'course_id'),
        Index('ix_course_materials_type', 'file_type'),
        Index('ix_course_materials_published', 'is_published'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship(
        "Course",
        foreign_keys=[course_id]
    )
    
    uploaded_by_user = relationship(
        "User",
        foreign_keys=[uploaded_by]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<CourseMaterial {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    @property
    def is_pdf(self) -> bool:
        """Check if material is a PDF."""
        return self.file_type == "pdf"
    
    @property
    def is_pptx(self) -> bool:
        """Check if material is a PPTX."""
        return self.file_type == "pptx"
    
    @property
    def is_doc(self) -> bool:
        """Check if material is a DOC."""
        return self.file_type in ["doc", "docx"]
    
    @property
    def is_actual_file(self) -> bool:
        """Check if material is a file (not a link)."""
        return not self.is_link
    
    @property
    def has_file(self) -> bool:
        """Check if material has a file URL."""
        return self.file_url is not None
    
    @property
    def has_link(self) -> bool:
        """Check if material has a link URL."""
        return self.link_url is not None
    
    @property
    def has_storage_path(self) -> bool:
        """Check if material has a storage path."""
        return self.storage_path is not None
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def publish(self) -> None:
        """Publish the material."""
        self.is_published = True
    
    def unpublish(self) -> None:
        """Unpublish the material."""
        self.is_published = False
    
    def soft_delete(self) -> None:
        """Soft delete the material."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted material."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def get_allowed_file_types() -> list:
        """Get list of allowed file types."""
        return ["pdf", "pptx", "doc", "docx", "png", "jpg", "jpeg", "gif", "webp"]
    
    @staticmethod
    def get_allowed_mime_types() -> dict:
        """Get mapping of file types to MIME types."""
        return {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
        }
    
    @staticmethod
    def get_max_file_size() -> int:
        """Get max file size in bytes."""
        return 20 * 1024 * 1024  # 20 MB
    
    @staticmethod
    def validate_file_type(file_type: str) -> bool:
        """Validate file type is allowed."""
        return file_type in CourseMaterial.get_allowed_file_types()
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size is within limit."""
        return file_size <= CourseMaterial.get_max_file_size()