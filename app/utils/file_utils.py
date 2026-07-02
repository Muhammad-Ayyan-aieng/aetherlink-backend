# ============================================================
# AETHER LINK - FILE UTILITIES
# ============================================================

import os
import re
import uuid
import mimetypes
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

# ============================================================
# CONSTANTS
# ============================================================

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    # Documents
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    
    # Images (for profile pictures)
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
}

# Maximum file size (20 MB)
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Magic bytes for file type verification
MAGIC_BYTES = {
    b'%PDF': 'pdf',
    b'PK\x03\x04': 'docx',  # Also matches pptx, docx, zip
    b'PK\x05\x06': 'docx',  # Empty zip
    b'PK\x07\x08': 'docx',  # Spanned zip
    b'\xff\xd8\xff': 'jpg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',  # Need further check for webp
    b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'doc',  # OLE2 format (doc, ppt, xls)
}


# ============================================================
# FILE EXTENSION UTILITIES
# ============================================================

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename (lowercase, without dot).
    
    Args:
        filename: Original filename
    
    Returns:
        File extension in lowercase
    
    Examples:
        >>> get_file_extension("document.pdf")
        "pdf"
        
        >>> get_file_extension("file.tar.gz")
        "gz"
    """
    if not filename:
        return ""
    
    # Get extension
    ext = os.path.splitext(filename)[1]
    
    # Remove dot and convert to lowercase
    return ext[1:].lower() if ext else ""


def get_all_extensions(filename: str) -> List[str]:
    """
    Get all extensions from filename (handles double extensions).
    
    Args:
        filename: Original filename
    
    Returns:
        List of all extensions
    
    Examples:
        >>> get_all_extensions("file.tar.gz")
        ["tar", "gz"]
        
        >>> get_all_extensions("file.jpg.exe")
        ["jpg", "exe"]
    """
    if not filename:
        return []
    
    parts = filename.split('.')
    if len(parts) <= 1:
        return []
    
    return [p.lower() for p in parts[1:]]


def get_mime_type(filename: str) -> str:
    """
    Get MIME type from file extension.
    
    Args:
        filename: Filename or extension
    
    Returns:
        MIME type string
    
    Examples:
        >>> get_mime_type("document.pdf")
        "application/pdf"
        
        >>> get_mime_type("image.jpg")
        "image/jpeg"
    """
    ext = get_file_extension(filename)
    
    if ext in ALLOWED_EXTENSIONS:
        return ALLOWED_EXTENSIONS[ext]
    
    # Fallback to mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove unsafe characters and paths.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    
    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        "etc_passwd"
        
        >>> sanitize_filename("file<script>.pdf")
        "file_script_.pdf"
    """
    if not filename:
        return ""

    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove dangerous characters (keep only alphanumeric, dots, underscores, hyphens)
    filename = re.sub(r'[^a-zA-Z0-9._\-]', '_', filename)
    
    # Remove consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing dots and underscores
    filename = filename.strip('._')
    
    # Truncate if too long
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        ext = ext[:10]  # Limit extension length
        name = name[:235]  # Leave room for extension
        filename = f"{name}{ext}"
    
    return filename or "file"


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename using UUID while preserving extension.
    
    Args:
        original_filename: Original filename
    
    Returns:
        Unique filename
    
    Examples:
        >>> generate_unique_filename("document.pdf")
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf"
    """
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    
    if ext:
        return f"{unique_id}.{ext}"
    return unique_id


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_file_extension(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Check if file extension is allowed.
    
    Args:
        filename: Original filename
        allowed_extensions: List of allowed extensions (uses ALLOWED_EXTENSIONS if None)
    
    Returns:
        True if extension is allowed
    
    Examples:
        >>> validate_file_extension("document.pdf")
        True
        
        >>> validate_file_extension("virus.exe")
        False
    """
    if not filename:
        return False
    
    if allowed_extensions is None:
        allowed_extensions = list(ALLOWED_EXTENSIONS.keys())
    
    ext = get_file_extension(filename)
    
    if not ext:
        return False
    
    # Check all extensions (prevents double extension attacks)
    all_exts = get_all_extensions(filename)
    
    # Check if ANY extension is not allowed
    for e in all_exts:
        if e not in allowed_extensions:
            return False
    
    return True


def validate_file_size(file_size: int, max_size_mb: int = MAX_FILE_SIZE_MB) -> bool:
    """
    Check if file size is within limit.
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB
    
    Returns:
        True if size is within limit
    
    Examples:
        >>> validate_file_size(1024 * 1024)  # 1 MB
        True
        
        >>> validate_file_size(25 * 1024 * 1024)  # 25 MB
        False
    """
    if file_size is None or file_size <= 0:
        return False
    
    max_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_bytes


def validate_file_content(file_content: bytes, expected_ext: Optional[str] = None) -> bool:
    """
    Validate file content using magic bytes.
    
    Args:
        file_content: First few bytes of file
        expected_ext: Expected file extension
    
    Returns:
        True if content matches expected type
    
    Examples:
        >>> validate_file_content(b'%PDF...', 'pdf')
        True
        
        >>> validate_file_content(b'PK\\x03\\x04...', 'docx')
        True
    """
    if not file_content:
        return False
    
    # Check against magic bytes
    detected_ext = None
    
    for magic, ext in MAGIC_BYTES.items():
        if file_content.startswith(magic):
            detected_ext = ext
            break
    
    # If we expected a specific extension, check if it matches
    if expected_ext:
        # For docx, pptx, zip (all use PK magic bytes)
        if expected_ext in ['docx', 'pptx'] and detected_ext in ['docx', 'pptx']:
            return True
        
        return detected_ext == expected_ext
    
    # If no expected extension, just check if we detected anything
    return detected_ext is not None


def validate_file(
    filename: str,
    file_content: Optional[bytes] = None,
    file_size: Optional[int] = None,
    allowed_extensions: Optional[List[str]] = None,
    max_size_mb: int = MAX_FILE_SIZE_MB,
    check_content: bool = True
) -> Dict[str, Any]:
    """
    Complete file validation.
    
    Args:
        filename: Original filename
        file_content: File content (for magic byte check)
        file_size: File size in bytes
        allowed_extensions: List of allowed extensions
        max_size_mb: Maximum file size in MB
        check_content: Whether to check file content with magic bytes
    
    Returns:
        Dictionary with validation results
    
    Examples:
        >>> validate_file("document.pdf", b'%PDF...', 1024)
        {"valid": True, "extension_valid": True, "size_valid": True, ...}
        
        >>> validate_file("virus.exe", b'MZ...', 1024)
        {"valid": False, "extension_valid": False, ...}
    """
    result = {
        "valid": False,
        "extension_valid": False,
        "size_valid": False,
        "content_valid": False,
        "errors": [],
        "filename": filename,
        "extension": get_file_extension(filename),
        "mime_type": get_mime_type(filename),
    }
    
    if not filename:
        result["errors"].append("Filename is required")
        return result
    
    # 1. Validate extension
    if allowed_extensions is None:
        allowed_extensions = list(ALLOWED_EXTENSIONS.keys())
    
    result["extension_valid"] = validate_file_extension(filename, allowed_extensions)
    if not result["extension_valid"]:
        result["errors"].append(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
    
    # 2. Validate size
    if file_size is not None:
        result["size_valid"] = validate_file_size(file_size, max_size_mb)
        result["file_size_bytes"] = file_size
        result["file_size_readable"] = get_human_readable_size(file_size)
        
        if not result["size_valid"]:
            result["errors"].append(f"File size exceeds {max_size_mb} MB limit")
    else:
        result["size_valid"] = True  # Skip size check if not provided
    
    # 3. Validate content (if provided)
    if file_content and check_content:
        expected_ext = result["extension"] if result["extension_valid"] else None
        result["content_valid"] = validate_file_content(file_content, expected_ext)
        
        if not result["content_valid"]:
            result["errors"].append("File content does not match file type")
    else:
        result["content_valid"] = True  # Skip content check if not provided
    
    # Overall validation
    result["valid"] = all([
        result["extension_valid"],
        result["size_valid"],
        result["content_valid"],
    ])
    
    return result


# ============================================================
# FILE SIZE UTILITIES
# ============================================================

def get_human_readable_size(size_bytes: int) -> str:
    """
    Convert bytes to human readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human readable size string
    
    Examples:
        >>> get_human_readable_size(1024)
        "1.00 KB"
        
        >>> get_human_readable_size(1048576)
        "1.00 MB"
    """
    if size_bytes is None or size_bytes <= 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def get_file_size_from_bytes(file_content: bytes) -> int:
    """
    Get file size from content.
    
    Args:
        file_content: File content as bytes
    
    Returns:
        Size in bytes
    """
    if not file_content:
        return 0
    return len(file_content)


# ============================================================
# FILE PATH UTILITIES
# ============================================================

def get_safe_file_path(base_path: str, filename: str) -> str:
    """
    Generate a safe file path to prevent directory traversal.
    
    Args:
        base_path: Base directory path
        filename: Sanitized filename
    
    Returns:
        Safe absolute file path
    
    Examples:
        >>> get_safe_file_path("/uploads", "file.pdf")
        "/uploads/file.pdf"
    """
    # Sanitize filename first
    safe_filename = sanitize_filename(filename)
    
    # Join paths
    full_path = os.path.join(base_path, safe_filename)
    
    # Ensure path is within base_path (prevent directory traversal)
    abs_base = os.path.abspath(base_path)
    abs_full = os.path.abspath(full_path)
    
    if not abs_full.startswith(abs_base):
        raise ValueError("Invalid file path: path traversal detected")
    
    return abs_full


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Constants
    'ALLOWED_EXTENSIONS',
    'MAX_FILE_SIZE_MB',
    'MAX_FILE_SIZE_BYTES',
    
    # Extensions
    'get_file_extension',
    'get_all_extensions',
    'get_mime_type',
    'sanitize_filename',
    'generate_unique_filename',
    
    # Validation
    'validate_file_extension',
    'validate_file_size',
    'validate_file_content',
    'validate_file',
    
    # Size utilities
    'get_human_readable_size',
    'get_file_size_from_bytes',
    
    # Path utilities
    'get_safe_file_path',
]