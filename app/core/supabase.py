# ============================================================
# AETHER LINK - SUPABASE STORAGE CLIENT
# ============================================================

import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile

from supabase import create_client, Client

from .config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Global client instance (singleton pattern)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    Uses singleton pattern for efficiency.
    
    Returns:
        Client: Supabase client instance
    
    Example:
        >>> client = get_supabase_client()
        >>> client.storage.from_("bucket").list()
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        logger.info(f"✅ Supabase client initialized for bucket: {settings.SUPABASE_BUCKET}")
    return _supabase_client


# ============================================================
# STORAGE OPERATIONS
# ============================================================

async def upload_file_to_storage(
    file: UploadFile,
    course_id: int,
    folder: str = "materials"
) -> Dict[str, Any]:
    """
    Upload a file to Supabase Storage.
    
    This function handles the complete upload process:
    1. Validates file extension against allowed types
    2. Validates MIME type
    3. Checks file size against configured limit
    4. Generates a unique UUID filename
    5. Uploads to Supabase Storage
    6. Returns metadata for database storage
    
    Args:
        file: UploadFile object from FastAPI
        course_id: Course ID (used in storage path)
        folder: Folder name inside course directory (default: "materials")
    
    Returns:
        Dict[str, Any]: File metadata containing:
            - storage_path: Full path in storage (e.g., "124/materials/uuid.pdf")
            - file_name: Original filename
            - file_size: Size in bytes
            - file_extension: File extension
            - mime_type: MIME type
    
    Raises:
        ValueError: If validation fails or upload fails
    
    Example:
        >>> result = await upload_file_to_storage(file, 124)
        >>> print(result["storage_path"])
        "124/materials/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    
    # ============================================================
    # 1. GET AND VALIDATE FILE EXTENSION
    # ============================================================
    
    file_extension = ""
    if file.filename and '.' in file.filename:
        file_extension = file.filename.rsplit('.', 1)[-1].lower()
    
    logger.info(f"📤 Uploading file: {file.filename}, extension: {file_extension}")
    
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise ValueError(
            f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )
    
    # ============================================================
    # 2. VALIDATE MIME TYPE
    # ============================================================
    
    if file.content_type and file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise ValueError(f"MIME type not allowed: {file.content_type}")
    
    # ============================================================
    # 3. READ AND VALIDATE FILE CONTENT
    # ============================================================
    
    content = await file.read()
    
    # Check file size
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB limit. "
            f"Current size: {len(content) / (1024 * 1024):.2f} MB"
        )
    
    # Check for empty file
    if len(content) == 0:
        raise ValueError("File is empty")
    
    # ============================================================
    # 4. GENERATE UNIQUE FILENAME
    # ============================================================
    
    unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
    
    # ============================================================
    # 5. BUILD STORAGE PATH
    # ============================================================
    
    # Format: {course_id}/{folder}/{unique_filename}
    storage_path = f"{course_id}/{folder}/{unique_filename}"
    logger.info(f"📁 Storage path: {storage_path}")
    
    # ============================================================
    # 6. UPLOAD TO SUPABASE STORAGE
    # ============================================================
    
    try:
        response = client.storage.from_(bucket).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": file.content_type or "application/octet-stream",
                "cache-control": "public, max-age=31536000, immutable"
            }
        )
        
        logger.info(f"✅ File uploaded successfully: {storage_path}")
        
        # Return metadata for database storage
        return {
            "storage_path": storage_path,
            "file_name": file.filename or unique_filename,
            "file_size": len(content),
            "file_extension": file_extension,
            "mime_type": file.content_type or "application/octet-stream",
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to upload file to storage: {e}")
        raise ValueError(f"Failed to upload file to storage: {str(e)}")


def delete_file_from_storage(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage.
    
    Args:
        storage_path: Full storage path (e.g., "124/materials/uuid.pdf")
    
    Returns:
        bool: True if deleted successfully, False if file not found
    
    Raises:
        ValueError: If delete fails for reasons other than file not found
    
    Example:
        >>> delete_file_from_storage("124/materials/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf")
        True
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    
    try:
        client.storage.from_(bucket).remove([storage_path])
        logger.info(f"🗑️ File deleted from storage: {storage_path}")
        return True
    except Exception as e:
        # Check if file not found (404 or "not found" in error message)
        if "not found" in str(e).lower() or "404" in str(e):
            logger.warning(f"⚠️ File not found in storage: {storage_path}")
            return False
        logger.error(f"❌ Failed to delete file from storage: {e}")
        raise ValueError(f"Failed to delete file from storage: {str(e)}")


def get_signed_url(storage_path: str, expires_in: int = 60) -> str:
    """
    Generate a signed URL for secure file access.
    
    Signed URLs provide temporary access to private files.
    The URL expires after the specified time.
    
    Args:
        storage_path: Full storage path (e.g., "124/materials/uuid.pdf")
        expires_in: URL expiry in seconds (default: 60)
    
    Returns:
        str: Signed URL for file access
    
    Raises:
        ValueError: If URL generation fails
    
    Example:
        >>> url = get_signed_url("124/materials/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf", 300)
        >>> print(url)
        "https://project.supabase.co/storage/v1/object/sign/..."
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    
    try:
        logger.info(f"🔐 Generating signed URL for: {storage_path} (expires in {expires_in}s)")
        response = client.storage.from_(bucket).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        
        signed_url = response.get("signedURL")
        if not signed_url:
            logger.error(f"❌ No signed URL returned. Response: {response}")
            raise ValueError("No signed URL returned from Supabase")
        
        logger.info(f"✅ Signed URL generated successfully")
        return signed_url
    except Exception as e:
        logger.error(f"❌ Failed to generate signed URL for {storage_path}: {e}")
        raise ValueError(f"Failed to generate signed URL: {str(e)}")


def file_exists(storage_path: str) -> bool:
    """
    Check if a file exists in Supabase Storage.
    
    Args:
        storage_path: Full storage path
    
    Returns:
        bool: True if file exists, False otherwise
    
    Example:
        >>> file_exists("124/materials/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf")
        True
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    
    try:
        # Get the folder path and filename
        folder = "/".join(storage_path.split("/")[:-1])
        filename = storage_path.split("/")[-1]
        
        # List files in the folder
        files = client.storage.from_(bucket).list(path=folder)
        
        # Check if the file exists
        exists = any(f.get("name") == filename for f in files)
        logger.info(f"📄 File exists check for {storage_path}: {exists}")
        return exists
    except Exception as e:
        logger.error(f"❌ Error checking file existence: {e}")
        return False


def get_public_url(storage_path: str) -> str:
    """
    Get the public URL for a file.
    
    Note: This only works if the bucket is public.
    For private buckets, use get_signed_url() instead.
    
    Args:
        storage_path: Full storage path
    
    Returns:
        str: Public URL of the file
    
    Example:
        >>> url = get_public_url("124/materials/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf")
        >>> print(url)
        "https://project.supabase.co/storage/v1/object/public/course-materials/..."
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET
    return client.storage.from_(bucket).get_public_url(storage_path)