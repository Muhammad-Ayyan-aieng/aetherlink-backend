# ============================================================
# AETHER LINK - CERTIFICATE MODEL
# ============================================================
# Purpose: Manage course completion certificates with:
# 1. QR code verification (public verification page)
# 2. Unique certificate numbers (AETH-CERT-YYYY-XXXXX)
# 3. Template-based PDF generation (upload template, fill placeholders)
# 4. Manual certificate upload support
# 5. Certificate revocation and audit
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, BigInteger, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import hashlib
import secrets
from ..core.database import Base


class CertificateStatus(str, enum.Enum):
    """Certificate status enumeration."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"
    GENERATING = "generating"
    FAILED = "failed"


class CertificateTemplateStatus(str, enum.Enum):
    """Certificate template status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CertificateGenerationMethod(str, enum.Enum):
    """How the certificate was generated."""
    TEMPLATE_AUTO = "template_auto"  # Auto-generated from template
    MANUAL_UPLOAD = "manual_upload"  # Manually uploaded PDF
    BULK_GENERATE = "bulk_generate"  # Batch generated


# ============================================================
# 1. CERTIFICATE TEMPLATE (Upload your design here)
# ============================================================

class CertificateTemplate(Base):
    """Certificate template with placeholders."""
    __tablename__ = "certificate_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template file (PDF with placeholders)
    template_file_url = Column(String(500), nullable=False)  # URL to template PDF
    template_file_name = Column(String(255), nullable=True)
    template_file_size = Column(BigInteger, nullable=True)
    
    # NEW: Template image (thumbnail/preview)
    preview_image_url = Column(String(500), nullable=True)
    
    # Placeholder mapping
    placeholders = Column(JSON, nullable=False)  # List of placeholders in template
    # Example: ["{{student_name}}", "{{course_name}}", "{{issue_date}}", "{{certificate_number}}"]
    
    # Default values for placeholders
    default_values = Column(JSON, nullable=True)
    # Example: {"issuer": "Aether Link", "issuer_logo": "https://...", "signature": "John Doe"}
    
    # Positioning (for text overlay)
    text_positions = Column(JSON, nullable=True)
    # Example: {"student_name": {"x": 100, "y": 200, "font_size": 24, "font_color": "#333333"}}
    
    # Status
    status = Column(
        String(20),
        default=CertificateTemplateStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    # NEW: Font settings
    font_family = Column(String(100), default="Arial", nullable=False)
    font_color = Column(String(7), default="#333333", nullable=False)
    accent_color = Column(String(7), default="#1A73E8", nullable=True)
    
    # NEW: Background
    background_image_url = Column(String(500), nullable=True)
    
    # NEW: Layout settings
    layout = Column(JSON, nullable=True)
    # Example: {"header": "Aether Link", "footer": "www.aetherlink.com"}
    
    # NEW: Certificate ID
    certificate_id_prefix = Column(String(20), default="AETH-CERT", nullable=False)
    
    # Created by
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    certificates = relationship("Certificate", foreign_keys=[template_id])
    
    __table_args__ = (
        Index('ix_cert_templates_status', 'status'),
        Index('ix_cert_templates_name', 'name'),
    )
    
    def __repr__(self) -> str:
        return f"<CertificateTemplate {self.name}>"
    
    @property
    def is_active(self) -> bool:
        """Check if template is active."""
        return self.status == CertificateTemplateStatus.ACTIVE.value
    
    @property
    def placeholder_list(self) -> list:
        """Get list of placeholder names."""
        if self.placeholders:
            return self.placeholders
        return []
    
    def get_placeholder_value(self, placeholder: str, context: dict) -> str:
        """Get value for a placeholder from context."""
        return context.get(placeholder.strip('{}'), "")
    
    def render_placeholders(self, context: dict) -> dict:
        """Render all placeholders with values."""
        result = {}
        for placeholder in self.placeholder_list:
            key = placeholder.strip('{}')
            result[placeholder] = context.get(key, "")
        return result


# ============================================================
# 2. CERTIFICATE (Main Model)
# ============================================================

class Certificate(Base):
    __tablename__ = "certificates"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # TEMPLATE REFERENCE
    # ============================================================
    template_id = Column(Integer, ForeignKey("certificate_templates.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # CERTIFICATE NUMBER ⭐ (UNIQUE)
    # ============================================================
    certificate_number = Column(String(50), nullable=False, unique=True, index=True)
    # Format: AETH-CERT-2026-000001
    
    # ============================================================
    # VERIFICATION HASH ⭐ (FOR TAMPER-PROOF VERIFICATION)
    # ============================================================
    verification_hash = Column(String(255), nullable=False, unique=True, index=True)
    # SHA-256 hash of certificate data
    
    # ============================================================
    # CERTIFICATE DETAILS
    # ============================================================
    issue_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)  # Optional expiry
    
    # Student details (snapshot at time of issuance)
    student_name = Column(String(255), nullable=False)
    student_email = Column(String(255), nullable=False)
    
    # Course details (snapshot at time of issuance)
    course_name = Column(String(255), nullable=False)
    course_level = Column(String(50), nullable=True)
    
    # Grade information
    grade = Column(String(10), nullable=True)  # A+, A, B, etc.
    score = Column(DECIMAL(5, 2), nullable=True)  # Percentage score
    performance_summary = Column(Text, nullable=True)
    
    # Skills achieved
    skills = Column(JSON, nullable=True)  # ["Python", "FastAPI", "PostgreSQL"]
    
    # ============================================================
    # GENERATION METHOD
    # ============================================================
    generation_method = Column(
        String(50),
        default=CertificateGenerationMethod.TEMPLATE_AUTO.value,
        nullable=False
    )
    
    # ============================================================
    # PDF GENERATION (From Template)
    # ============================================================
    pdf_url = Column(String(500), nullable=True)  # URL to final PDF
    pdf_generated_at = Column(DateTime(timezone=True), nullable=True)
    pdf_version = Column(Integer, default=1, nullable=False)
    
    # PDF generation status
    pdf_status = Column(String(20), default="pending", nullable=False)  # pending, generating, completed, failed
    pdf_error = Column(Text, nullable=True)
    
    # ============================================================
    # MANUAL UPLOAD (For manually uploaded certificates)
    # ============================================================
    is_manual = Column(Boolean, default=False, nullable=False)
    manual_pdf_url = Column(String(500), nullable=True)  # Manually uploaded PDF
    manual_uploaded_at = Column(DateTime(timezone=True), nullable=True)
    manual_uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    manual_notes = Column(Text, nullable=True)
    
    # ============================================================
    # QR CODE ⭐
    # ============================================================
    qr_code_url = Column(String(500), nullable=True)  # URL to QR code image
    qr_code_data = Column(String(500), nullable=True)  # Data encoded in QR
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=CertificateStatus.PENDING.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # REVOCATION TRACKING
    # ============================================================
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # ============================================================
    # EXPIRY TRACKING
    # ============================================================
    expired_at = Column(DateTime(timezone=True), nullable=True)
    expiry_notification_sent = Column(Boolean, default=False, nullable=False)
    expiry_notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # VERIFICATION STATISTICS
    # ============================================================
    verification_count = Column(Integer, default=0, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_verified_by_ip = Column(String(100), nullable=True)
    
    # ============================================================
    # SHARING
    # ============================================================
    share_count = Column(Integer, default=0, nullable=False)
    last_shared_at = Column(DateTime(timezone=True), nullable=True)
    share_links = Column(JSON, nullable=True)  # Track shared links
    
    # ============================================================
    # METADATA
    # ============================================================
    metadata = Column(JSON, nullable=True)
    
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
        Index('ix_certificates_number_status', 'certificate_number', 'status'),
        Index('ix_certificates_student_status', 'student_id', 'status'),
        Index('ix_certificates_course_status', 'course_id', 'status'),
        Index('ix_certificates_issue_date', 'issue_date'),
        Index('ix_certificates_hash', 'verification_hash'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    enrollment = relationship(
        "Enrollment",
        foreign_keys=[enrollment_id],
        uselist=False
    )
    
    student = relationship(
        "User",
        back_populates="certificates",
        foreign_keys=[student_id]
    )
    
    course = relationship(
        "Course",
        foreign_keys=[course_id]
    )
    
    template = relationship(
        "CertificateTemplate",
        foreign_keys=[template_id]
    )
    
    revoked_by_user = relationship(
        "User",
        back_populates="revoked_certificates",
        foreign_keys=[revoked_by],
        uselist=False
    )
    
    manual_uploaded_by_user = relationship(
        "User",
        foreign_keys=[manual_uploaded_by],
        uselist=False
    )
    
    verification_logs = relationship(
        "CertificateVerificationLog",
        back_populates="certificate",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Certificate {self.certificate_number} - {self.status}>"
    
    def __str__(self) -> str:
        return f"{self.certificate_number} - {self.student_name}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active(self) -> bool:
        """Check if certificate is active."""
        return self.status == CertificateStatus.ACTIVE.value and not self.is_expired
    
    @property
    def is_revoked(self) -> bool:
        """Check if certificate is revoked."""
        return self.status == CertificateStatus.REVOKED.value
    
    @property
    def is_expired(self) -> bool:
        """Check if certificate has expired."""
        if self.expiry_date is None:
            return False
        return self.expiry_date <= func.now()
    
    @property
    def is_verified(self) -> bool:
        """Check if certificate has been verified at least once."""
        return self.verification_count > 0
    
    @property
    def is_manual_certificate(self) -> bool:
        """Check if certificate was manually uploaded."""
        return self.is_manual
    
    @property
    def is_template_generated(self) -> bool:
        """Check if certificate was generated from template."""
        return not self.is_manual and self.generation_method == CertificateGenerationMethod.TEMPLATE_AUTO.value
    
    @property
    def has_pdf(self) -> bool:
        """Check if certificate has a PDF (auto or manual)."""
        return self.pdf_url is not None or self.manual_pdf_url is not None
    
    @property
    def final_pdf_url(self) -> str:
        """Get the final PDF URL (prefers manual if exists)."""
        if self.manual_pdf_url:
            return self.manual_pdf_url
        return self.pdf_url
    
    @property
    def verification_url(self) -> str:
        """Get public verification URL."""
        return f"https://aetherlink.com/verify/{self.certificate_number}"
    
    @property
    def qr_code_data_full(self) -> dict:
        """Get full QR code data."""
        return {
            "type": "certificate",
            "issuer": "Aether Link",
            "certificate_number": self.certificate_number,
            "verification_url": self.verification_url,
            "hash": self.verification_hash,
            "student_name": self.student_name,
            "course_name": self.course_name,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
        }
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_revoked:
            return "Revoked"
        elif self.is_expired:
            return "Expired"
        elif self.is_active:
            return "Active"
        return self.status.title()
    
    @property
    def age_days(self) -> int:
        """Get certificate age in days."""
        if self.issue_date is None:
            return 0
        delta = func.now() - self.issue_date
        return delta.days
    
    @property
    def grade_display(self) -> str:
        """Get human-readable grade."""
        if not self.grade:
            return "Not Graded"
        return self.grade
    
    # ============================================================
    # METHODS ⭐ (CRITICAL)
    # ============================================================
    
    def generate_certificate_number(self) -> str:
        """
        Generate a unique certificate number.
        Format: AETH-CERT-YYYY-XXXXXX
        """
        year = func.extract('year', func.now())
        # This will be implemented in the service layer with DB sequence
        return f"AETH-CERT-{year}-000001"  # Placeholder
    
    def generate_verification_hash(self) -> str:
        """
        Generate a verification hash.
        Used for tamper-proof verification.
        """
        data = f"{self.certificate_number}{self.student_id}{self.course_id}{self.issue_date}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generate_qr_data(self) -> str:
        """Generate data to encode in QR code."""
        import json
        return json.dumps(self.qr_code_data_full)
    
    def revoke(self, revoked_by: int, reason: str) -> None:
        """
        Revoke the certificate.
        
        Args:
            revoked_by: Admin ID who revoked
            reason: Reason for revocation
        """
        self.status = CertificateStatus.REVOKED.value
        self.revoked_at = func.now()
        self.revoked_by = revoked_by
        self.revocation_reason = reason
    
    def expire(self) -> None:
        """Mark certificate as expired."""
        self.status = CertificateStatus.EXPIRED.value
        self.expired_at = func.now()
    
    def mark_generating(self) -> None:
        """Mark certificate as generating."""
        self.status = CertificateStatus.GENERATING.value
        self.pdf_status = "generating"
    
    def mark_generated(self, pdf_url: str) -> None:
        """Mark certificate as generated."""
        self.status = CertificateStatus.ACTIVE.value
        self.pdf_url = pdf_url
        self.pdf_generated_at = func.now()
        self.pdf_status = "completed"
        self.pdf_version += 1
    
    def mark_failed(self, error: str = None) -> None:
        """Mark certificate generation as failed."""
        self.status = CertificateStatus.FAILED.value
        self.pdf_status = "failed"
        if error:
            self.pdf_error = error
    
    def set_qr_code(self, qr_code_url: str) -> None:
        """Set QR code image URL."""
        self.qr_code_url = qr_code_url
    
    def increment_verification(self, ip_address: str = None) -> None:
        """Increment verification count."""
        self.verification_count += 1
        self.last_verified_at = func.now()
        if ip_address:
            self.last_verified_by_ip = ip_address
    
    def increment_share(self) -> None:
        """Increment share count."""
        self.share_count += 1
        self.last_shared_at = func.now()
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete(self) -> None:
        """Soft delete the certificate."""
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted certificate."""
        self.deleted_at = None
    
    # ============================================================
    # MANUAL UPLOAD METHODS
    # ============================================================
    
    def upload_manual_certificate(self, pdf_url: str, uploaded_by: int, notes: str = None) -> None:
        """
        Upload a manually created certificate PDF.
        
        Args:
            pdf_url: URL to the uploaded PDF
            uploaded_by: Admin ID who uploaded
            notes: Optional notes about the certificate
        """
        self.is_manual = True
        self.manual_pdf_url = pdf_url
        self.manual_uploaded_at = func.now()
        self.manual_uploaded_by = uploaded_by
        if notes:
            self.manual_notes = notes
        self.status = CertificateStatus.ACTIVE.value
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    @staticmethod
    def validate_certificate_number(cert_number: str) -> bool:
        """Validate certificate number format."""
        import re
        pattern = r'^AETH-CERT-[0-9]{4}-[0-9]{6,}$'
        return bool(re.match(pattern, cert_number))
    
    @staticmethod
    def validate_grade(grade: str) -> bool:
        """Validate grade."""
        valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"]
        return grade in valid_grades if grade else True
    
    @staticmethod
    def validate_score(score: float) -> bool:
        """Validate score."""
        return 0 <= score <= 100 if score is not None else True
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert certificate to dictionary."""
        data = {
            "id": self.id,
            "certificate_number": self.certificate_number,
            "verification_url": self.verification_url,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "student_email": self.student_email,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "course_level": self.course_level,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "status": self.status,
            "display_status": self.display_status,
            "is_active": self.is_active,
            "is_revoked": self.is_revoked,
            "is_expired": self.is_expired,
            "is_manual": self.is_manual,
            "is_template_generated": self.is_template_generated,
            "grade": self.grade,
            "grade_display": self.grade_display,
            "score": float(self.score) if self.score else None,
            "skills": self.skills,
            "performance_summary": self.performance_summary,
            "verification_count": self.verification_count,
            "is_verified": self.is_verified,
            "share_count": self.share_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "verification_hash": self.verification_hash,
                "qr_code_url": self.qr_code_url,
                "qr_code_data": self.qr_code_data,
                "pdf_url": self.pdf_url,
                "manual_pdf_url": self.manual_pdf_url,
                "final_pdf_url": self.final_pdf_url,
                "pdf_generated_at": self.pdf_generated_at.isoformat() if self.pdf_generated_at else None,
                "pdf_status": self.pdf_status,
                "pdf_error": self.pdf_error,
                "pdf_version": self.pdf_version,
                "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
                "revoked_by": self.revoked_by,
                "revocation_reason": self.revocation_reason,
                "expired_at": self.expired_at.isoformat() if self.expired_at else None,
                "manual_uploaded_at": self.manual_uploaded_at.isoformat() if self.manual_uploaded_at else None,
                "manual_uploaded_by": self.manual_uploaded_by,
                "manual_notes": self.manual_notes,
                "template_id": self.template_id,
                "generation_method": self.generation_method,
                "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
                "last_verified_by_ip": self.last_verified_by_ip,
                "last_shared_at": self.last_shared_at.isoformat() if self.last_shared_at else None,
                "share_links": self.share_links,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing certificate data (for verification page)."""
        return {
            "certificate_number": self.certificate_number,
            "student_name": self.student_name,
            "course_name": self.course_name,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "status": self.display_status,
            "is_valid": self.is_active,
            "grade": self.grade_display,
            "skills": self.skills,
        }
    
    def to_student_json(self) -> dict:
        """Student-facing certificate data."""
        data = self.to_dict()
        data.update({
            "qr_code_data": self.qr_code_data,
            "verification_url": self.verification_url,
            "can_download": self.has_pdf,
            "download_url": self.final_pdf_url,
        })
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing certificate data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 3. CERTIFICATE VERIFICATION LOG
# ============================================================

class CertificateVerificationLog(Base):
    """Track every verification attempt (for QR code scans)."""
    __tablename__ = "certificate_verification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Verification details
    method = Column(
        String(50),
        default=CertificateVerificationMethod.QR_SCAN.value,
        nullable=False
    )
    success = Column(Boolean, default=True, nullable=False)
    status_at_verification = Column(String(20), nullable=True)  # Status of cert when verified
    
    # Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Location (geo-ip)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    
    # Referrer (where did they come from)
    referrer_url = Column(String(500), nullable=True)
    
    # Timestamp
    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # NEW: Details
    details = Column(JSON, nullable=True)
    
    # Relationships
    certificate = relationship("Certificate", back_populates="verification_logs")
    
    __table_args__ = (
        Index('ix_cert_verification_cert_date', 'certificate_id', 'verified_at'),
        Index('ix_cert_verification_ip', 'ip_address'),
    )
    
    def __repr__(self) -> str:
        return f"<CertificateVerificationLog {self.id}: {self.certificate_id}>"


# ============================================================
# 4. CERTIFICATE SETTINGS
# ============================================================

class CertificateSettings(Base):
    """System-wide certificate settings."""
    __tablename__ = "certificate_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Default template
    default_template_id = Column(Integer, ForeignKey("certificate_templates.id", ondelete="SET NULL"), nullable=True)
    
    # Auto-issue settings
    auto_issue_on_completion = Column(Boolean, default=True, nullable=False)
    auto_issue_delay_hours = Column(Integer, default=0, nullable=False)  # Delay after completion
    
    # Expiry settings
    default_expiry_days = Column(Integer, nullable=True)  # Null = no expiry
    
    # QR Code settings
    qr_code_size = Column(Integer, default=200, nullable=False)
    qr_code_color = Column(String(7), default="#000000", nullable=False)
    qr_code_bg_color = Column(String(7), default="#FFFFFF", nullable=False)
    
    # Email settings
    send_email_on_issue = Column(Boolean, default=True, nullable=False)
    send_email_on_revoke = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    default_template = relationship("CertificateTemplate", foreign_keys=[default_template_id])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self) -> str:
        return "<CertificateSettings>"


# ============================================================
# 5. BULK CERTIFICATE GENERATION BATCH
# ============================================================

class CertificateBatch(Base):
    """Batch certificate generation jobs."""
    __tablename__ = "certificate_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Batch details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template
    template_id = Column(Integer, ForeignKey("certificate_templates.id", ondelete="SET NULL"), nullable=True)
    
    # Target
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    enrollment_ids = Column(JSON, nullable=True)  # Specific enrollments
    
    # Status
    status = Column(String(20), default="draft", nullable=False)  # draft, processing, completed, failed
    
    # Statistics
    total_count = Column(Integer, default=0, nullable=False)
    generated_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    # Created by
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    template = relationship("CertificateTemplate", foreign_keys=[template_id])
    course = relationship("Course", foreign_keys=[course_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index('ix_cert_batches_status', 'status'),
        Index('ix_cert_batches_course', 'course_id'),
    )
    
    def __repr__(self) -> str:
        return f"<CertificateBatch {self.id}: {self.name}>"
    
    @property
    def is_processing(self) -> bool:
        """Check if batch is processing."""
        return self.status == "processing"
    
    @property
    def is_completed(self) -> bool:
        """Check if batch is completed."""
        return self.status == "completed"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_count == 0:
            return 0.0
        return (self.generated_count / self.total_count) * 100
    
    def mark_processing(self) -> None:
        """Mark batch as processing."""
        self.status = "processing"
    
    def mark_completed(self) -> None:
        """Mark batch as completed."""
        self.status = "completed"
        self.completed_at = func.now()
    
    def mark_failed(self) -> None:
        """Mark batch as failed."""
        self.status = "failed"
        self.completed_at = func.now()