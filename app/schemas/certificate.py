# ============================================================
# AETHER LINK - CERTIFICATE SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# CERTIFICATE ENUMS
# ============================================================

class CertificateStatusEnum(str, Enum):
    """Certificate status enumeration."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"
    GENERATING = "generating"
    FAILED = "failed"


class CertificateTemplateStatusEnum(str, Enum):
    """Certificate template status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CertificateGenerationMethodEnum(str, Enum):
    """Certificate generation method."""
    TEMPLATE_AUTO = "template_auto"
    MANUAL_UPLOAD = "manual_upload"
    BULK_GENERATE = "bulk_generate"


class CertificateVerificationMethodEnum(str, Enum):
    """Certificate verification method."""
    QR_SCAN = "qr_scan"
    MANUAL = "manual"
    API = "api"
    PUBLIC_PAGE = "public_page"


# ============================================================
# BASE SCHEMA
# ============================================================

class CertificateBase(BaseModel):
    """Base certificate schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# CERTIFICATE TEMPLATE SCHEMAS
# ============================================================

class CertificateTemplateCreate(CertificateBase):
    """Schema for creating a certificate template."""
    
    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    description: Optional[str] = Field(default=None, max_length=500, description="Template description")
    
    # Template file (PDF with placeholders)
    template_file_url: str = Field(..., max_length=500, description="Template PDF URL")
    template_file_name: Optional[str] = Field(default=None, max_length=255, description="Template file name")
    template_file_size: Optional[int] = Field(default=None, ge=0, description="Template file size in bytes")
    
    # Preview image
    preview_image_url: Optional[str] = Field(default=None, max_length=500, description="Preview image URL")
    
    # Placeholders
    placeholders: List[str] = Field(..., min_length=1, description="List of placeholders")
    # Example: ["student_name", "course_name", "issue_date", "certificate_number"]
    
    # Default values for placeholders
    default_values: Optional[Dict[str, str]] = Field(default=None, description="Default values for placeholders")
    
    # Text positioning
    text_positions: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Text positioning for placeholders"
    )
    # Example: {"student_name": {"x": 100, "y": 200, "font_size": 24, "font_color": "#333333"}}
    
    # Styling
    font_family: str = Field(default="Arial", max_length=100, description="Font family")
    font_color: str = Field(default="#333333", max_length=7, description="Font color (hex)")
    accent_color: Optional[str] = Field(default="#1A73E8", max_length=7, description="Accent color (hex)")
    
    # Background
    background_image_url: Optional[str] = Field(default=None, max_length=500, description="Background image URL")
    
    # Layout
    layout: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Layout settings"
    )
    # Example: {"header": "Aether Link", "footer": "www.aetherlink.com"}
    
    # Certificate ID prefix
    certificate_id_prefix: str = Field(default="AETH-CERT", max_length=20, description="Certificate ID prefix")
    
    # Status
    status: CertificateTemplateStatusEnum = Field(
        default=CertificateTemplateStatusEnum.DRAFT,
        description="Template status"
    )


class CertificateTemplateUpdate(CertificateBase):
    """Schema for updating a certificate template."""
    
    name: Optional[str] = Field(default=None, min_length=3, max_length=100, description="Template name")
    description: Optional[str] = Field(default=None, max_length=500, description="Template description")
    
    template_file_url: Optional[str] = Field(default=None, max_length=500, description="Template PDF URL")
    template_file_name: Optional[str] = Field(default=None, max_length=255, description="Template file name")
    preview_image_url: Optional[str] = Field(default=None, max_length=500, description="Preview image URL")
    
    placeholders: Optional[List[str]] = Field(default=None, description="List of placeholders")
    default_values: Optional[Dict[str, str]] = Field(default=None, description="Default values")
    text_positions: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="Text positioning")
    
    font_family: Optional[str] = Field(default=None, max_length=100, description="Font family")
    font_color: Optional[str] = Field(default=None, max_length=7, description="Font color (hex)")
    accent_color: Optional[str] = Field(default=None, max_length=7, description="Accent color (hex)")
    background_image_url: Optional[str] = Field(default=None, max_length=500, description="Background image URL")
    layout: Optional[Dict[str, Any]] = Field(default=None, description="Layout settings")
    certificate_id_prefix: Optional[str] = Field(default=None, max_length=20, description="Certificate ID prefix")
    
    status: Optional[CertificateTemplateStatusEnum] = Field(default=None, description="Template status")


class CertificateTemplateResponse(CertificateBase):
    """Schema for certificate template response."""
    
    id: int = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(default=None, description="Template description")
    
    template_file_url: str = Field(..., description="Template PDF URL")
    template_file_name: Optional[str] = Field(default=None, description="Template file name")
    template_file_size: Optional[int] = Field(default=None, description="Template file size")
    preview_image_url: Optional[str] = Field(default=None, description="Preview image URL")
    
    placeholders: List[str] = Field(default_factory=list, description="Placeholders")
    default_values: Optional[Dict[str, str]] = Field(default=None, description="Default values")
    text_positions: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="Text positioning")
    
    font_family: str = Field(default="Arial", description="Font family")
    font_color: str = Field(default="#333333", description="Font color")
    accent_color: Optional[str] = Field(default=None, description="Accent color")
    background_image_url: Optional[str] = Field(default=None, description="Background image URL")
    layout: Optional[Dict[str, Any]] = Field(default=None, description="Layout settings")
    
    certificate_id_prefix: str = Field(default="AETH-CERT", description="Certificate ID prefix")
    status: str = Field(..., description="Template status")
    is_active: bool = Field(..., description="Is template active")
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CERTIFICATE GENERATE SCHEMA
# ============================================================

class CertificateGenerate(CertificateBase):
    """Schema for generating a certificate."""
    
    enrollment_id: int = Field(..., gt=0, description="Enrollment ID")
    template_id: Optional[int] = Field(default=None, gt=0, description="Template ID (uses default if None)")
    
    # NEW: Manual override for certificate data
    student_name_override: Optional[str] = Field(default=None, max_length=255, description="Override student name")
    course_name_override: Optional[str] = Field(default=None, max_length=255, description="Override course name")
    issue_date_override: Optional[datetime] = Field(default=None, description="Override issue date")
    
    # NEW: Custom placeholders
    custom_placeholders: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom placeholder values"
    )
    
    # NEW: Grade/Score
    grade: Optional[str] = Field(default=None, max_length=10, description="Grade (A+, A, B, etc.)")
    score: Optional[float] = Field(default=None, ge=0, le=100, description="Score percentage")
    performance_summary: Optional[str] = Field(default=None, max_length=500, description="Performance summary")
    skills: Optional[List[str]] = Field(default=None, description="Skills achieved")


class CertificateManualUpload(CertificateBase):
    """Schema for manually uploading a certificate PDF."""
    
    enrollment_id: int = Field(..., gt=0, description="Enrollment ID")
    pdf_url: str = Field(..., max_length=500, description="Certificate PDF URL")
    notes: Optional[str] = Field(default=None, max_length=500, description="Upload notes")


# ============================================================
# CERTIFICATE REVOKE SCHEMA
# ============================================================

class CertificateRevoke(CertificateBase):
    """Schema for revoking a certificate."""
    
    certificate_id: int = Field(..., gt=0, description="Certificate ID")
    reason: str = Field(..., min_length=5, max_length=500, description="Revocation reason")


# ============================================================
# CERTIFICATE VERIFY SCHEMA (Public)
# ============================================================

class CertificateVerify(CertificateBase):
    """Schema for public certificate verification."""
    
    certificate_number: str = Field(..., description="Certificate number to verify")


class CertificateVerifyResponse(CertificateBase):
    """Schema for public certificate verification response."""
    
    is_valid: bool = Field(..., description="Is certificate valid")
    student_name: Optional[str] = Field(default=None, description="Student name")
    course_name: Optional[str] = Field(default=None, description="Course name")
    issue_date: Optional[datetime] = Field(default=None, description="Issue date")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date")
    grade: Optional[str] = Field(default=None, description="Grade")
    skills: Optional[List[str]] = Field(default=None, description="Skills achieved")
    status: str = Field(..., description="Certificate status")
    message: Optional[str] = Field(default=None, description="Verification message")
    verified_at: Optional[datetime] = Field(default=None, description="Verification timestamp")


# ============================================================
# CERTIFICATE BULK GENERATE SCHEMA
# ============================================================

class CertificateBulkGenerate(CertificateBase):
    """Schema for bulk certificate generation."""
    
    course_id: int = Field(..., gt=0, description="Course ID")
    enrollment_ids: Optional[List[int]] = Field(default=None, description="Specific enrollment IDs")
    template_id: Optional[int] = Field(default=None, gt=0, description="Template ID")
    
    # NEW: Filters
    only_completed: bool = Field(default=True, description="Only generate for completed enrollments")
    only_verified: bool = Field(default=True, description="Only generate for verified students")
    
    # NEW: Notification
    notify_students: bool = Field(default=True, description="Notify students via email")


class CertificateBulkGenerateResponse(CertificateBase):
    """Schema for bulk generation response."""
    
    batch_id: int = Field(..., description="Batch ID")
    total: int = Field(..., description="Total enrollments")
    generated: int = Field(..., description="Generated certificates")
    failed: int = Field(..., description="Failed certificates")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")
    status: str = Field(..., description="Batch status")


# ============================================================
# CERTIFICATE RESPONSE SCHEMA
# ============================================================

class CertificateResponse(CertificateBase):
    """Schema for certificate response."""
    
    id: int = Field(..., description="Certificate ID")
    certificate_number: str = Field(..., description="Certificate number")
    verification_hash: str = Field(..., description="Verification hash")
    verification_url: str = Field(..., description="Public verification URL")
    
    enrollment_id: int = Field(..., description="Enrollment ID")
    student_id: int = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    student_email: str = Field(..., description="Student email")
    
    course_id: int = Field(..., description="Course ID")
    course_name: str = Field(..., description="Course name")
    course_level: Optional[str] = Field(default=None, description="Course level")
    
    # NEW: Template
    template_id: Optional[int] = Field(default=None, description="Template ID")
    
    issue_date: datetime = Field(..., description="Issue date")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date")
    
    grade: Optional[str] = Field(default=None, description="Grade")
    score: Optional[float] = Field(default=None, description="Score percentage")
    performance_summary: Optional[str] = Field(default=None, description="Performance summary")
    skills: Optional[List[str]] = Field(default=None, description="Skills achieved")
    
    # NEW: QR Code
    qr_code_url: Optional[str] = Field(default=None, description="QR code image URL")
    qr_code_data: Optional[str] = Field(default=None, description="QR code data")
    
    # NEW: PDF
    pdf_url: Optional[str] = Field(default=None, description="PDF download URL")
    pdf_generated_at: Optional[datetime] = Field(default=None, description="PDF generation timestamp")
    pdf_version: int = Field(default=1, description="PDF version")
    
    # NEW: Generation method
    generation_method: str = Field(..., description="Generation method")
    is_manual: bool = Field(default=False, description="Is manually uploaded")
    is_template_generated: bool = Field(default=True, description="Is template generated")
    
    status: str = Field(..., description="Certificate status")
    display_status: str = Field(..., description="Human-readable status")
    is_active: bool = Field(..., description="Is certificate active")
    is_revoked: bool = Field(..., description="Is certificate revoked")
    is_expired: bool = Field(..., description="Is certificate expired")
    
    # NEW: Verification statistics
    verification_count: int = Field(default=0, description="Number of verifications")
    is_verified: bool = Field(default=False, description="Has been verified")
    last_verified_at: Optional[datetime] = Field(default=None, description="Last verification timestamp")
    
    # NEW: Sharing statistics
    share_count: int = Field(default=0, description="Number of shares")
    last_shared_at: Optional[datetime] = Field(default=None, description="Last share timestamp")
    
    # NEW: Revocation info
    revoked_at: Optional[datetime] = Field(default=None, description="Revocation timestamp")
    revoked_by: Optional[int] = Field(default=None, description="Revoked by user ID")
    revocation_reason: Optional[str] = Field(default=None, description="Revocation reason")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CERTIFICATE PUBLIC RESPONSE (Public Verification Page)
# ============================================================

class CertificatePublicResponse(CertificateBase):
    """Schema for public certificate verification page."""
    
    certificate_number: str = Field(..., description="Certificate number")
    student_name: str = Field(..., description="Student name")
    course_name: str = Field(..., description="Course name")
    issue_date: datetime = Field(..., description="Issue date")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date")
    
    grade: Optional[str] = Field(default=None, description="Grade")
    skills: Optional[List[str]] = Field(default=None, description="Skills achieved")
    
    status: str = Field(..., description="Certificate status")
    is_valid: bool = Field(..., description="Is certificate valid")
    message: Optional[str] = Field(default=None, description="Verification message")
    
    # NEW: Issuer info
    issuer_name: str = Field(default="Aether Link", description="Issuer name")
    issuer_logo_url: Optional[str] = Field(default=None, description="Issuer logo URL")
    issuer_website: Optional[str] = Field(default=None, description="Issuer website")


# ============================================================
# CERTIFICATE LIST REQUEST (Filters)
# ============================================================

class CertificateListRequest(CertificateBase):
    """Schema for certificate list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by certificate number or student name")
    status: Optional[CertificateStatusEnum] = Field(default=None, description="Filter by status")
    student_id: Optional[int] = Field(default=None, description="Filter by student")
    course_id: Optional[int] = Field(default=None, description="Filter by course")
    is_manual: Optional[bool] = Field(default=None, description="Filter by manual upload")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# CERTIFICATE LIST RESPONSE
# ============================================================

class CertificateListResponse(CertificateBase):
    """Schema for paginated certificate list response."""
    
    certificates: List[CertificateResponse] = Field(..., description="List of certificates")
    total: int = Field(..., description="Total certificates")
    active_count: int = Field(..., description="Active certificates")
    revoked_count: int = Field(..., description="Revoked certificates")
    expired_count: int = Field(..., description="Expired certificates")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# CERTIFICATE STATISTICS
# ============================================================

class CertificateStatistics(CertificateBase):
    """Schema for certificate statistics."""
    
    total_issued: int = Field(..., description="Total certificates issued")
    active: int = Field(..., description="Active certificates")
    revoked: int = Field(..., description="Revoked certificates")
    expired: int = Field(..., description="Expired certificates")
    
    # NEW: By generation method
    template_generated: int = Field(..., description="Template generated")
    manually_uploaded: int = Field(..., description="Manually uploaded")
    bulk_generated: int = Field(..., description="Bulk generated")
    
    # NEW: Verification stats
    total_verifications: int = Field(..., description="Total verifications")
    unique_verified_certificates: int = Field(..., description="Unique certificates verified")
    average_verifications: float = Field(..., description="Average verifications per certificate")
    
    # NEW: By course
    course_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Certificates by course"
    )
    
    # NEW: Trends
    monthly_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Monthly issuance trends"
    )


# ============================================================
# CERTIFICATE SHARE SCHEMA
# ============================================================

class CertificateShare(CertificateBase):
    """Schema for sharing a certificate."""
    
    certificate_id: int = Field(..., gt=0, description="Certificate ID")
    platform: str = Field(..., description="Platform to share on")
    # Example: linkedin, twitter, facebook, whatsapp, email


class CertificateShareResponse(CertificateBase):
    """Schema for certificate share response."""
    
    success: bool = Field(..., description="Share success")
    share_url: Optional[str] = Field(default=None, description="Share URL")
    message: str = Field(..., description="Share message")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CertificateStatusEnum",
    "CertificateTemplateStatusEnum",
    "CertificateGenerationMethodEnum",
    "CertificateVerificationMethodEnum",
    "CertificateTemplateCreate",
    "CertificateTemplateUpdate",
    "CertificateTemplateResponse",
    "CertificateGenerate",
    "CertificateManualUpload",
    "CertificateRevoke",
    "CertificateVerify",
    "CertificateVerifyResponse",
    "CertificateBulkGenerate",
    "CertificateBulkGenerateResponse",
    "CertificateResponse",
    "CertificatePublicResponse",
    "CertificateListRequest",
    "CertificateListResponse",
    "CertificateStatistics",
    "CertificateShare",
    "CertificateShareResponse",
]