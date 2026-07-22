# ============================================================
# AETHER LINK - COURSE MATERIAL MODEL (UPGRADED)
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class MaterialType(str, enum.Enum):  # NEW
    """Material type enumeration."""
    PDF = "pdf"
    PPTX = "pptx"
    DOC = "doc"
    DOCX = "docx"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    LINK = "link"
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    ZOOM = "zoom"
    TEXT = "text"
    OTHER = "other"


class MaterialVisibility(str, enum.Enum):  # NEW
    """Material visibility enumeration."""
    PUBLIC = "public"
    ENROLLED_ONLY = "enrolled_only"
    TEACHER_ONLY = "teacher_only"
    ADMIN_ONLY = "admin_only"


class Material(Base):
    __tablename__ = "materials"  # Changed from course_materials

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # COURSE RELATIONSHIP
    # ============================================================
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Session relationship (optional - material can be linked to a session)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # NEW: Material type (enum)
    material_type = Column(
        String(50),
        default=MaterialType.OTHER.value,
        nullable=False,
        index=True
    )
    
    # NEW: Legacy file_type (keep for compatibility)
    file_type = Column(String(50), nullable=True)
    
    # ============================================================
    # FILE INFORMATION
    # ============================================================
    file_url = Column(String(500), nullable=True)           # Cloud storage URL
    file_name = Column(String(255), nullable=True)          # Original file name
    
    # NEW: File hash (for deduplication)
    file_hash = Column(String(255), nullable=True, index=True)
    
    file_size = Column(BigInteger, nullable=True)           # Size in bytes (BigInteger for large files)
    mime_type = Column(String(100), nullable=True)          # application/pdf, etc.
    
    # ============================================================
    # SUPABASE STORAGE
    # ============================================================
    storage_path = Column(String(500), nullable=True)       # Path in Supabase Storage
    storage_bucket = Column(String(100), nullable=True)     # Bucket name
    
    # ============================================================
    # LINK INFORMATION
    # ============================================================
    is_link = Column(Boolean, default=False, nullable=False)  # True if it's a link
    link_url = Column(String(500), nullable=True)             # YouTube/Vimeo link
    
    # NEW: Video specific fields
    video_duration_seconds = Column(Integer, nullable=True)   # For video files
    video_thumbnail_url = Column(String(500), nullable=True)  # Video thumbnail
    video_platform = Column(String(50), nullable=True)        # youtube, vimeo, custom
    
    # NEW: Is this a recording of a session?
    is_recording = Column(Boolean, default=False, nullable=False, index=True)
    recording_session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # PUBLISHING & VISIBILITY
    # ============================================================
    is_published = Column(Boolean, default=True, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Visibility control
    visibility = Column(
        String(50),
        default=MaterialVisibility.ENROLLED_ONLY.value,
        nullable=False
    )
    
    # NEW: Access password (optional)
    access_password = Column(String(255), nullable=True)  # Hashed
    
    # ============================================================
    # UPLOADER
    # ============================================================
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Last editor
    last_edited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # NEW: VIEW & DOWNLOAD STATISTICS
    # ============================================================
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    # Example: {"pages": 10, "author": "John", "resolution": "1080p"}
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_materials_course', 'course_id'),
        Index('ix_materials_session', 'session_id'),
        Index('ix_materials_type', 'material_type'),
        Index('ix_materials_published', 'is_published'),
        Index('ix_materials_visibility', 'visibility'),
        Index('ix_materials_is_recording', 'is_recording'),
        Index('ix_materials_uploaded_by', 'uploaded_by'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    course = relationship(
        "Course",
        back_populates="materials",
        foreign_keys=[course_id]
    )
    
    # NEW: Session relationship
    session = relationship(
        "Session",
        foreign_keys=[session_id],
        uselist=False
    )
    
    uploaded_by_user = relationship(
        "User",
        foreign_keys=[uploaded_by]
    )
    
    # NEW: Last editor relationship
    last_edited_by_user = relationship(
        "User",
        foreign_keys=[last_edited_by],
        uselist=False
    )
    
    # NEW: Video watch progress (for recordings)
    watch_progress = relationship(
        "VideoWatchProgress",
        back_populates="material",
        cascade="all, delete-orphan"
    )
    
    # NEW: Session materials (many-to-many)
    session_materials = relationship(
        "SessionMaterial",
        back_populates="material",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Material {self.title}>"
    
    def __str__(self) -> str:
        return self.title
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_pdf(self) -> bool:
        """Check if material is a PDF."""
        return self.material_type == MaterialType.PDF.value
    
    @property
    def is_pptx(self) -> bool:
        """Check if material is a PPTX."""
        return self.material_type == MaterialType.PPTX.value
    
    @property
    def is_doc(self) -> bool:
        """Check if material is a DOC."""
        return self.material_type in [MaterialType.DOC.value, MaterialType.DOCX.value]
    
    @property
    def is_video(self) -> bool:
        """Check if material is a video."""
        return self.material_type == MaterialType.VIDEO.value
    
    @property
    def is_audio(self) -> bool:
        """Check if material is audio."""
        return self.material_type == MaterialType.AUDIO.value
    
    @property
    def is_image(self) -> bool:
        """Check if material is an image."""
        return self.material_type == MaterialType.IMAGE.value
    
    @property
    def is_youtube(self) -> bool:
        """Check if material is a YouTube link."""
        return self.material_type == MaterialType.YOUTUBE.value
    
    @property
    def is_actual_file(self) -> bool:
        """Check if material is a file (not a link)."""
        return not self.is_link and self.file_url is not None
    
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
    
    @property
    def is_public(self) -> bool:
        """Check if material is public."""
        return self.visibility == MaterialVisibility.PUBLIC.value
    
    @property
    def is_enrolled_only(self) -> bool:
        """Check if material is for enrolled students only."""
        return self.visibility == MaterialVisibility.ENROLLED_ONLY.value
    
    @property
    def is_teacher_only(self) -> bool:
        """Check if material is for teachers only."""
        return self.visibility == MaterialVisibility.TEACHER_ONLY.value
    
    @property
    def display_type(self) -> str:
        """Get human-readable material type."""
        type_map = {
            "pdf": "PDF",
            "pptx": "PowerPoint",
            "doc": "Word Document",
            "docx": "Word Document",
            "video": "Video",
            "audio": "Audio",
            "image": "Image",
            "link": "Link",
            "youtube": "YouTube",
            "vimeo": "Vimeo",
            "zoom": "Zoom Recording",
            "text": "Text",
            "other": "Other",
        }
        return type_map.get(self.material_type, "File")
    
    @property
    def icon_class(self) -> str:
        """Get icon class for UI."""
        icon_map = {
            "pdf": "fa-file-pdf",
            "pptx": "fa-file-powerpoint",
            "doc": "fa-file-word",
            "docx": "fa-file-word",
            "video": "fa-file-video",
            "audio": "fa-file-audio",
            "image": "fa-file-image",
            "link": "fa-link",
            "youtube": "fa-youtube",
            "vimeo": "fa-vimeo",
            "text": "fa-file-alt",
            "other": "fa-file",
        }
        return icon_map.get(self.material_type, "fa-file")
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def publish(self) -> None:
        """Publish the material."""
        self.is_published = True
        self.published_at = func.now()
    
    def unpublish(self) -> None:
        """Unpublish the material."""
        self.is_published = False
    
    def increment_view(self) -> None:
        """Increment view count."""
        self.view_count += 1
        self.last_viewed_at = func.now()
    
    def increment_download(self) -> None:
        """Increment download count."""
        self.download_count += 1
        self.last_downloaded_at = func.now()
    
    def set_as_recording(self, session_id: int, duration_seconds: int = None) -> None:
        """Set material as a recording of a session."""
        self.is_recording = True
        self.recording_session_id = session_id
        if duration_seconds:
            self.video_duration_seconds = duration_seconds
    
    def set_visibility(self, visibility: str) -> None:
        """Set material visibility."""
        if visibility in [v.value for v in MaterialVisibility]:
            self.visibility = visibility
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete(self) -> None:
        """Soft delete the material."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted material."""
        self.deleted_at = None
    
    def set_file_info(self, url: str, file_name: str, file_type: str, size: int, mime_type: str = None, storage_path: str = None) -> None:
        """Set file information."""
        self.file_url = url
        self.file_name = file_name
        self.material_type = file_type
        self.file_size = size
        if mime_type:
            self.mime_type = mime_type
        if storage_path:
            self.storage_path = storage_path
    
    def set_link(self, url: str, link_type: str) -> None:
        """Set link information."""
        self.is_link = True
        self.link_url = url
        self.material_type = link_type
    
    def set_video_metadata(self, duration_seconds: int, thumbnail_url: str = None, platform: str = None) -> None:
        """Set video metadata."""
        self.video_duration_seconds = duration_seconds
        if thumbnail_url:
            self.video_thumbnail_url = thumbnail_url
        if platform:
            self.video_platform = platform
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def get_allowed_file_types() -> list:
        """Get list of allowed file types."""
        return ["pdf", "pptx", "doc", "docx", "png", "jpg", "jpeg", "gif", "webp", "mp4", "webm", "mp3", "wav"]
    
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
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
        }
    
    @staticmethod
    def get_max_file_size() -> int:
        """Get max file size in bytes (20MB for documents, 200MB for videos)."""
        return 200 * 1024 * 1024  # 200 MB
    
    @staticmethod
    def validate_file_type(file_type: str) -> bool:
        """Validate file type is allowed."""
        return file_type in Material.get_allowed_file_types()
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size is within limit."""
        return file_size <= Material.get_max_file_size()
    
    @staticmethod
    def is_video_file(file_type: str) -> bool:
        """Check if file type is a video."""
        return file_type in ["mp4", "webm", "avi", "mov", "mkv"]
    
    @staticmethod
    def is_audio_file(file_type: str) -> bool:
        """Check if file type is audio."""
        return file_type in ["mp3", "wav", "aac", "flac", "ogg"]
    
    @staticmethod
    def is_image_file(file_type: str) -> bool:
        """Check if file type is an image."""
        return file_type in ["png", "jpg", "jpeg", "gif", "webp", "svg"]
    
    @staticmethod
    def is_document_file(file_type: str) -> bool:
        """Check if file type is a document."""
        return file_type in ["pdf", "pptx", "doc", "docx", "xls", "xlsx"]
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert material to dictionary."""
        data = {
            "id": self.id,
            "course_id": self.course_id,
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "material_type": self.material_type,
            "display_type": self.display_type,
            "icon_class": self.icon_class,
            "is_link": self.is_link,
            "is_recording": self.is_recording,
            "is_published": self.is_published,
            "visibility": self.visibility,
            "is_public": self.is_public,
            "is_enrolled_only": self.is_enrolled_only,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "size_mb": self.size_mb,
            "mime_type": self.mime_type,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "video_duration_seconds": self.video_duration_seconds,
            "video_thumbnail_url": self.video_thumbnail_url,
            "video_platform": self.video_platform,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
        
        if include_sensitive:
            data.update({
                "file_url": self.file_url,
                "link_url": self.link_url,
                "storage_path": self.storage_path,
                "storage_bucket": self.storage_bucket,
                "file_hash": self.file_hash,
                "access_password": self.access_password,
                "last_edited_by": self.last_edited_by,
                "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None,
                "last_downloaded_at": self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
                "recording_session_id": self.recording_session_id,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing material data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("file_url", None)
        data.pop("storage_path", None)
        data.pop("storage_bucket", None)
        data.pop("file_hash", None)
        data.pop("access_password", None)
        data.pop("metadata", None)
        
        # Only include link_url if it's a link
        if self.is_link and self.link_url:
            data["link_url"] = self.link_url
        elif not self.is_link:
            data["file_url"] = self.file_url  # Public URL (not sensitive)
        
        return data
    
    def to_student_json(self) -> dict:
        """Student-facing material data."""
        data = self.to_public_json()
        data.update({
            "can_access": self.is_published and (self.is_public or self.is_enrolled_only),
            "is_available": self.is_published,
        })
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing material data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# NEW: MATERIAL VIEW LOG (Audit Trail)
# ============================================================

class MaterialViewLog(Base):
    """Track material views for analytics."""
    __tablename__ = "material_view_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # View details
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True)  # How long they viewed
    view_type = Column(String(50), nullable=True)  # preview, full, download
    
    # Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    
    # Relationships
    material = relationship("Material", foreign_keys=[material_id])
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<MaterialViewLog {self.id}: {self.material_id} - {self.user_id}>"