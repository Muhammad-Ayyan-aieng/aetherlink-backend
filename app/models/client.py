# ============================================================
# AETHER LINK - CLIENT MODEL (Software House)
# ============================================================
# Purpose: Manage Software House clients and their information
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class ClientStatus(str, enum.Enum):
    """Client status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"
    PROSPECT = "prospect"
    FORMER = "former"
    BLACKLISTED = "blacklisted"


class ClientType(str, enum.Enum):
    """Client type enumeration."""
    INDIVIDUAL = "individual"
    COMPANY = "company"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    EDUCATIONAL = "educational"


class ClientIndustry(str, enum.Enum):
    """Client industry enumeration."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    HOSPITALITY = "hospitality"
    CONSULTING = "consulting"
    OTHER = "other"


class ContactRole(str, enum.Enum):
    """Contact person role enumeration."""
    PRIMARY = "primary"
    BILLING = "billing"
    TECHNICAL = "technical"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    OTHER = "other"


# ============================================================
# 1. CLIENT MODEL
# ============================================================

class Client(Base):
    __tablename__ = "clients"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    company_name = Column(String(255), nullable=False)
    trading_name = Column(String(255), nullable=True)
    
    # NEW: Client type
    client_type = Column(
        String(50),
        default=ClientType.COMPANY.value,
        nullable=False
    )
    
    # NEW: Industry
    industry = Column(
        String(50),
        default=ClientIndustry.OTHER.value,
        nullable=False
    )
    
    # ============================================================
    # CONTACT INFORMATION
    # ============================================================
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    alternate_phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    
    # ============================================================
    # ADDRESS
    # ============================================================
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # ============================================================
    # COMPANY DETAILS
    # ============================================================
    registration_number = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)  # GST/VAT
    company_size = Column(String(50), nullable=True)  # 1-10, 11-50, 51-200, 201-500, 500+
    founded_year = Column(Integer, nullable=True)
    
    # NEW: Company logo
    logo_url = Column(String(500), nullable=True)
    
    # ============================================================
    # BILLING INFORMATION
    # ============================================================
    billing_address = Column(Text, nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_phone = Column(String(50), nullable=True)
    payment_terms = Column(String(100), nullable=True)  # Net 30, Net 60, etc.
    credit_limit = Column(DECIMAL(12, 2), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=ClientStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    # NEW: Priority (for support/service)
    priority = Column(Integer, default=1, nullable=False)  # 1=Normal, 2=High, 3=VIP
    
    # ============================================================
    # REFERRAL
    # ============================================================
    referred_by = Column(String(255), nullable=True)
    referral_source = Column(String(255), nullable=True)
    
    # ============================================================
    # ASSIGNED TO
    # ============================================================
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # CREATOR
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # NEW: SOCIAL MEDIA
    # ============================================================
    social_links = Column(JSON, nullable=True)
    # Example: {"linkedin": "https://...", "twitter": "https://...", "facebook": "https://..."}
    
    # ============================================================
    # NEW: METADATA
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
        Index('ix_clients_email', 'email'),
        Index('ix_clients_company_name', 'company_name'),
        Index('ix_clients_status', 'status'),
        Index('ix_clients_industry', 'industry'),
        Index('ix_clients_assigned_to', 'assigned_to'),
        Index('ix_clients_created_by', 'created_by'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    assigned_to_user = relationship(
        "User",
        foreign_keys=[assigned_to],
        uselist=False
    )
    
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        uselist=False
    )
    
    # NEW: Contact persons
    contacts = relationship(
        "ClientContact",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    # NEW: Projects
    projects = relationship(
        "ClientProject",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    # NEW: Invoices
    invoices = relationship(
        "Invoice",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    # NEW: Communications
    communications = relationship(
        "ClientCommunication",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Client {self.id}: {self.company_name}>"
    
    def __str__(self) -> str:
        return self.company_name
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active_client(self) -> bool:
        """Check if client is active."""
        return self.status == ClientStatus.ACTIVE.value
    
    @property
    def is_lead(self) -> bool:
        """Check if client is a lead."""
        return self.status == ClientStatus.LEAD.value
    
    @property
    def is_prospect(self) -> bool:
        """Check if client is a prospect."""
        return self.status == ClientStatus.PROSPECT.value
    
    @property
    def is_former_client(self) -> bool:
        """Check if client is former."""
        return self.status == ClientStatus.FORMER.value
    
    @property
    def is_blacklisted(self) -> bool:
        """Check if client is blacklisted."""
        return self.status == ClientStatus.BLACKLISTED.value
    
    @property
    def is_vip(self) -> bool:
        """Check if client is VIP."""
        return self.priority >= 3
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "active": "🟢 Active",
            "inactive": "⚪ Inactive",
            "lead": "🟡 Lead",
            "prospect": "🔵 Prospect",
            "former": "⚫ Former",
            "blacklisted": "🔴 Blacklisted",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def display_industry(self) -> str:
        """Get human-readable industry."""
        industry_map = {
            "technology": "💻 Technology",
            "healthcare": "🏥 Healthcare",
            "finance": "💰 Finance",
            "education": "📚 Education",
            "retail": "🛒 Retail",
            "manufacturing": "🏭 Manufacturing",
            "real_estate": "🏠 Real Estate",
            "hospitality": "🏨 Hospitality",
            "consulting": "📊 Consulting",
            "other": "📌 Other",
        }
        return industry_map.get(self.industry, "Other")
    
    @property
    def display_client_type(self) -> str:
        """Get human-readable client type."""
        type_map = {
            "individual": "👤 Individual",
            "company": "🏢 Company",
            "government": "🏛️ Government",
            "non_profit": "🤝 Non-Profit",
            "educational": "🎓 Educational",
        }
        return type_map.get(self.client_type, "Company")
    
    @property
    def project_count(self) -> int:
        """Get number of projects."""
        return len(self.projects) if self.projects else 0
    
    @property
    def active_project_count(self) -> int:
        """Get number of active projects."""
        if not self.projects:
            return 0
        return sum(1 for p in self.projects if p.is_active)
    
    @property
    def total_revenue(self) -> float:
        """Get total revenue from all invoices."""
        if not self.invoices:
            return 0.0
        return sum(float(i.total_amount) for i in self.invoices if i.is_paid)
    
    @property
    def has_contacts(self) -> bool:
        """Check if client has contact persons."""
        return len(self.contacts) > 0 if self.contacts else False
    
    @property
    def primary_contact(self):
        """Get primary contact person."""
        if not self.contacts:
            return None
        primary = [c for c in self.contacts if c.role == ContactRole.PRIMARY.value]
        return primary[0] if primary else self.contacts[0]
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def activate(self) -> None:
        """Activate the client."""
        self.status = ClientStatus.ACTIVE.value
    
    def deactivate(self) -> None:
        """Deactivate the client."""
        self.status = ClientStatus.INACTIVE.value
    
    def mark_as_lead(self) -> None:
        """Mark client as lead."""
        self.status = ClientStatus.LEAD.value
    
    def mark_as_prospect(self) -> None:
        """Mark client as prospect."""
        self.status = ClientStatus.PROSPECT.value
    
    def mark_as_former(self) -> None:
        """Mark client as former."""
        self.status = ClientStatus.FORMER.value
    
    def blacklist(self) -> None:
        """Blacklist the client."""
        self.status = ClientStatus.BLACKLISTED.value
    
    def set_priority(self, priority: int) -> None:
        """Set client priority (1-3)."""
        if 1 <= priority <= 3:
            self.priority = priority
    
    def set_assigned_to(self, user_id: int) -> None:
        """Assign client to a team member."""
        self.assigned_to = user_id
    
    def add_contact(self, contact: 'ClientContact') -> None:
        """Add a contact person."""
        if self.contacts is None:
            self.contacts = []
        self.contacts.append(contact)
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def soft_delete_client(self) -> None:
        """Soft delete the client."""
        self.deleted_at = func.now()
    
    def restore_client(self) -> None:
        """Restore a soft-deleted client."""
        self.deleted_at = None
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number."""
        if not phone:
            return True
        import re
        return bool(re.match(r'^[0-9+\-\(\) ]+$', phone))
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert client to dictionary."""
        data = {
            "id": self.id,
            "company_name": self.company_name,
            "trading_name": self.trading_name,
            "client_type": self.client_type,
            "display_client_type": self.display_client_type,
            "industry": self.industry,
            "display_industry": self.display_industry,
            "email": self.email,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "website": self.website,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "registration_number": self.registration_number,
            "tax_id": self.tax_id,
            "company_size": self.company_size,
            "founded_year": self.founded_year,
            "logo_url": self.logo_url,
            "status": self.status,
            "display_status": self.display_status,
            "priority": self.priority,
            "is_vip": self.is_vip,
            "referred_by": self.referred_by,
            "referral_source": self.referral_source,
            "assigned_to": self.assigned_to,
            "assigned_to_name": self.assigned_to_user.full_name if self.assigned_to_user else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "project_count": self.project_count,
            "active_project_count": self.active_project_count,
            "total_revenue": self.total_revenue,
            "primary_contact": self.primary_contact.to_dict() if self.primary_contact else None,
            "social_links": self.social_links,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "billing_address": self.billing_address,
                "billing_email": self.billing_email,
                "billing_phone": self.billing_phone,
                "payment_terms": self.payment_terms,
                "credit_limit": float(self.credit_limit) if self.credit_limit else None,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing client data."""
        data = self.to_dict()
        data.pop("registration_number", None)
        data.pop("tax_id", None)
        data.pop("credit_limit", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing client data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. CLIENT CONTACT PERSON MODEL
# ============================================================

class ClientContact(Base):
    __tablename__ = "client_contacts"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================================
    # CONTACT INFORMATION
    # ============================================================
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    alternate_phone = Column(String(50), nullable=True)
    
    # ============================================================
    # ROLE
    # ============================================================
    role = Column(
        String(50),
        default=ContactRole.OTHER.value,
        nullable=False
    )
    
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    is_active = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # NEW: SOCIAL MEDIA
    # ============================================================
    social_links = Column(JSON, nullable=True)
    
    # ============================================================
    # NEW: NOTES
    # ============================================================
    notes = Column(Text, nullable=True)
    
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
        Index('ix_client_contacts_client', 'client_id'),
        Index('ix_client_contacts_email', 'email'),
        Index('ix_client_contacts_active', 'is_active'),
        Index('ix_client_contacts_primary', 'is_primary'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    client = relationship(
        "Client",
        back_populates="contacts",
        foreign_keys=[client_id]
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<ClientContact {self.id}: {self.full_name}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def display_role(self) -> str:
        """Get human-readable role."""
        role_map = {
            "primary": "⭐ Primary",
            "billing": "💰 Billing",
            "technical": "🔧 Technical",
            "manager": "👔 Manager",
            "executive": "🏛️ Executive",
            "other": "📌 Other",
        }
        return role_map.get(self.role, "Other")
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def set_as_primary(self) -> None:
        """Set this contact as primary."""
        self.is_primary = True
    
    def unset_primary(self) -> None:
        """Unset primary status."""
        self.is_primary = False
    
    def soft_delete_contact(self) -> None:
        """Soft delete the contact."""
        self.deleted_at = func.now()
    
    def restore_contact(self) -> None:
        """Restore a soft-deleted contact."""
        self.deleted_at = None
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self) -> dict:
        """Convert contact to dictionary."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "role": self.role,
            "display_role": self.display_role,
            "job_title": self.job_title,
            "department": self.department,
            "is_active": self.is_active,
            "is_primary": self.is_primary,
            "social_links": self.social_links,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# 3. CLIENT COMMUNICATION MODEL
# ============================================================

class ClientCommunication(Base):
    """Track client communications (calls, emails, meetings)."""
    __tablename__ = "client_communications"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Communication type
    communication_type = Column(String(50), nullable=False)  # email, call, meeting, message, note
    
    # Content
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # NEW: Scheduled for
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Completed at
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Attachments
    attachments = Column(JSON, nullable=True)
    
    # NEW: Created by
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Assigned to
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Status
    status = Column(String(20), default="pending", nullable=False)  # pending, completed, cancelled
    
    # NEW: Follow-up
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    client = relationship("Client", back_populates="communications")
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    __table_args__ = (
        Index('ix_client_communications_client', 'client_id'),
        Index('ix_client_communications_created_by', 'created_by'),
        Index('ix_client_communications_assigned_to', 'assigned_to'),
        Index('ix_client_communications_scheduled', 'scheduled_at'),
        Index('ix_client_communications_type', 'communication_type'),
    )
    
    def __repr__(self) -> str:
        return f"<ClientCommunication {self.id}: {self.subject}>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "communication_type": self.communication_type,
            "subject": self.subject,
            "content": self.content,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attachments": self.attachments,
            "created_by": self.created_by,
            "created_by_name": self.creator.full_name if self.creator else None,
            "assigned_to": self.assigned_to,
            "assigned_to_name": self.assignee.full_name if self.assignee else None,
            "status": self.status,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "follow_up_notes": self.follow_up_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }