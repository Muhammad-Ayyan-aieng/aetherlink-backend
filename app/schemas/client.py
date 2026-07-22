# ============================================================
# AETHER LINK - CLIENT SCHEMAS (Software House)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# CLIENT ENUMS
# ============================================================

class ClientStatusEnum(str, Enum):
    """Client status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"
    PROSPECT = "prospect"
    FORMER = "former"
    BLACKLISTED = "blacklisted"


class ClientTypeEnum(str, Enum):
    """Client type enumeration."""
    INDIVIDUAL = "individual"
    COMPANY = "company"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    EDUCATIONAL = "educational"


class ClientIndustryEnum(str, Enum):
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


class ContactRoleEnum(str, Enum):
    """Contact person role enumeration."""
    PRIMARY = "primary"
    BILLING = "billing"
    TECHNICAL = "technical"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    OTHER = "other"


# ============================================================
# BASE SCHEMA
# ============================================================

class ClientBase(BaseModel):
    """Base client schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# CLIENT CREATE SCHEMA
# ============================================================

class ClientCreate(ClientBase):
    """Schema for creating a client."""
    
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    trading_name: Optional[str] = Field(default=None, max_length=255, description="Trading name")
    
    client_type: ClientTypeEnum = Field(
        default=ClientTypeEnum.COMPANY,
        description="Client type"
    )
    industry: ClientIndustryEnum = Field(
        default=ClientIndustryEnum.OTHER,
        description="Industry"
    )
    
    email: EmailStr = Field(..., description="Primary email")
    phone: Optional[str] = Field(default=None, max_length=50, description="Phone number")
    alternate_phone: Optional[str] = Field(default=None, max_length=50, description="Alternate phone")
    website: Optional[str] = Field(default=None, max_length=500, description="Website URL")
    
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Address line 1")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(default=None, max_length=100, description="City")
    state: Optional[str] = Field(default=None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(default=None, max_length=20, description="Postal code")
    country: Optional[str] = Field(default=None, max_length=100, description="Country")
    
    registration_number: Optional[str] = Field(default=None, max_length=100, description="Registration number")
    tax_id: Optional[str] = Field(default=None, max_length=100, description="Tax ID (GST/VAT)")
    company_size: Optional[str] = Field(default=None, max_length=50, description="Company size")
    founded_year: Optional[int] = Field(default=None, ge=1900, le=datetime.now().year, description="Founded year")
    
    logo_url: Optional[str] = Field(default=None, max_length=500, description="Logo URL")
    
    billing_address: Optional[str] = Field(default=None, max_length=500, description="Billing address")
    billing_email: Optional[EmailStr] = Field(default=None, description="Billing email")
    billing_phone: Optional[str] = Field(default=None, max_length=50, description="Billing phone")
    payment_terms: Optional[str] = Field(default=None, max_length=100, description="Payment terms")
    credit_limit: Optional[float] = Field(default=None, ge=0, description="Credit limit")
    
    status: ClientStatusEnum = Field(
        default=ClientStatusEnum.ACTIVE,
        description="Client status"
    )
    priority: int = Field(default=1, ge=1, le=3, description="Priority (1=Normal, 2=High, 3=VIP)")
    
    referred_by: Optional[str] = Field(default=None, max_length=255, description="Referred by")
    referral_source: Optional[str] = Field(default=None, max_length=255, description="Referral source")
    
    assigned_to: Optional[int] = Field(default=None, gt=0, description="Assigned to user ID")
    
    social_links: Optional[Dict[str, str]] = Field(
        default=None,
        description="Social media links"
    )
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL."""
        if v is None or v == "":
            return v
        if not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v


# ============================================================
# CLIENT UPDATE SCHEMA
# ============================================================

class ClientUpdate(ClientBase):
    """Schema for updating a client."""
    
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=255, description="Company name")
    trading_name: Optional[str] = Field(default=None, max_length=255, description="Trading name")
    
    client_type: Optional[ClientTypeEnum] = Field(default=None, description="Client type")
    industry: Optional[ClientIndustryEnum] = Field(default=None, description="Industry")
    
    email: Optional[EmailStr] = Field(default=None, description="Primary email")
    phone: Optional[str] = Field(default=None, max_length=50, description="Phone number")
    alternate_phone: Optional[str] = Field(default=None, max_length=50, description="Alternate phone")
    website: Optional[str] = Field(default=None, max_length=500, description="Website URL")
    
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Address line 1")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(default=None, max_length=100, description="City")
    state: Optional[str] = Field(default=None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(default=None, max_length=20, description="Postal code")
    country: Optional[str] = Field(default=None, max_length=100, description="Country")
    
    registration_number: Optional[str] = Field(default=None, max_length=100, description="Registration number")
    tax_id: Optional[str] = Field(default=None, max_length=100, description="Tax ID")
    company_size: Optional[str] = Field(default=None, max_length=50, description="Company size")
    founded_year: Optional[int] = Field(default=None, ge=1900, description="Founded year")
    
    logo_url: Optional[str] = Field(default=None, max_length=500, description="Logo URL")
    
    billing_address: Optional[str] = Field(default=None, max_length=500, description="Billing address")
    billing_email: Optional[EmailStr] = Field(default=None, description="Billing email")
    billing_phone: Optional[str] = Field(default=None, max_length=50, description="Billing phone")
    payment_terms: Optional[str] = Field(default=None, max_length=100, description="Payment terms")
    credit_limit: Optional[float] = Field(default=None, ge=0, description="Credit limit")
    
    status: Optional[ClientStatusEnum] = Field(default=None, description="Client status")
    priority: Optional[int] = Field(default=None, ge=1, le=3, description="Priority (1=Normal, 2=High, 3=VIP)")
    
    referred_by: Optional[str] = Field(default=None, max_length=255, description="Referred by")
    referral_source: Optional[str] = Field(default=None, max_length=255, description="Referral source")
    
    assigned_to: Optional[int] = Field(default=None, gt=0, description="Assigned to user ID")
    
    social_links: Optional[Dict[str, str]] = Field(
        default=None,
        description="Social media links"
    )


# ============================================================
# CLIENT CONTACT SCHEMAS
# ============================================================

class ClientContactCreate(ClientBase):
    """Schema for creating a client contact."""
    
    client_id: int = Field(..., gt=0, description="Client ID")
    
    full_name: str = Field(..., min_length=2, max_length=255, description="Contact full name")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(default=None, max_length=50, description="Phone number")
    alternate_phone: Optional[str] = Field(default=None, max_length=50, description="Alternate phone")
    
    role: ContactRoleEnum = Field(
        default=ContactRoleEnum.OTHER,
        description="Contact role"
    )
    job_title: Optional[str] = Field(default=None, max_length=100, description="Job title")
    department: Optional[str] = Field(default=None, max_length=100, description="Department")
    
    is_active: bool = Field(default=True, description="Is active")
    is_primary: bool = Field(default=False, description="Is primary contact")
    
    social_links: Optional[Dict[str, str]] = Field(
        default=None,
        description="Social media links"
    )
    notes: Optional[str] = Field(default=None, max_length=500, description="Notes")


class ClientContactUpdate(ClientBase):
    """Schema for updating a client contact."""
    
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255, description="Contact full name")
    email: Optional[EmailStr] = Field(default=None, description="Contact email")
    phone: Optional[str] = Field(default=None, max_length=50, description="Phone number")
    alternate_phone: Optional[str] = Field(default=None, max_length=50, description="Alternate phone")
    
    role: Optional[ContactRoleEnum] = Field(default=None, description="Contact role")
    job_title: Optional[str] = Field(default=None, max_length=100, description="Job title")
    department: Optional[str] = Field(default=None, max_length=100, description="Department")
    
    is_active: Optional[bool] = Field(default=None, description="Is active")
    is_primary: Optional[bool] = Field(default=None, description="Is primary contact")
    
    social_links: Optional[Dict[str, str]] = Field(
        default=None,
        description="Social media links"
    )
    notes: Optional[str] = Field(default=None, max_length=500, description="Notes")


class ClientContactResponse(ClientBase):
    """Schema for client contact response."""
    
    id: int = Field(..., description="Contact ID")
    client_id: int = Field(..., description="Client ID")
    
    full_name: str = Field(..., description="Contact full name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(default=None, description="Phone number")
    alternate_phone: Optional[str] = Field(default=None, description="Alternate phone")
    
    role: str = Field(..., description="Contact role")
    display_role: str = Field(..., description="Human-readable role")
    job_title: Optional[str] = Field(default=None, description="Job title")
    department: Optional[str] = Field(default=None, description="Department")
    
    is_active: bool = Field(..., description="Is active")
    is_primary: bool = Field(..., description="Is primary contact")
    
    social_links: Optional[Dict[str, str]] = Field(
        default=None,
        description="Social media links"
    )
    notes: Optional[str] = Field(default=None, description="Notes")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CLIENT COMMUNICATION SCHEMAS
# ============================================================

class ClientCommunicationCreate(ClientBase):
    """Schema for creating a client communication."""
    
    client_id: int = Field(..., gt=0, description="Client ID")
    
    communication_type: str = Field(..., description="Communication type (email, call, meeting, message, note)")
    subject: str = Field(..., min_length=1, max_length=255, description="Subject")
    content: str = Field(..., min_length=1, max_length=5000, description="Content")
    
    scheduled_at: Optional[datetime] = Field(default=None, description="Scheduled timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completed timestamp")
    
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    
    assigned_to: Optional[int] = Field(default=None, gt=0, description="Assigned to user ID")
    
    status: str = Field(default="pending", description="Status (pending, completed, cancelled)")
    
    follow_up_date: Optional[datetime] = Field(default=None, description="Follow-up date")
    follow_up_notes: Optional[str] = Field(default=None, max_length=500, description="Follow-up notes")


class ClientCommunicationUpdate(ClientBase):
    """Schema for updating a client communication."""
    
    content: Optional[str] = Field(default=None, max_length=5000, description="Content")
    status: Optional[str] = Field(default=None, description="Status")
    completed_at: Optional[datetime] = Field(default=None, description="Completed timestamp")
    follow_up_date: Optional[datetime] = Field(default=None, description="Follow-up date")
    follow_up_notes: Optional[str] = Field(default=None, max_length=500, description="Follow-up notes")


class ClientCommunicationResponse(ClientBase):
    """Schema for client communication response."""
    
    id: int = Field(..., description="Communication ID")
    client_id: int = Field(..., description="Client ID")
    
    communication_type: str = Field(..., description="Communication type")
    subject: str = Field(..., description="Subject")
    content: str = Field(..., description="Content")
    
    scheduled_at: Optional[datetime] = Field(default=None, description="Scheduled timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completed timestamp")
    
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Attachments"
    )
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    assigned_to: Optional[int] = Field(default=None, description="Assigned to user ID")
    assigned_to_name: Optional[str] = Field(default=None, description="Assigned to user name")
    
    status: str = Field(..., description="Status")
    
    follow_up_date: Optional[datetime] = Field(default=None, description="Follow-up date")
    follow_up_notes: Optional[str] = Field(default=None, description="Follow-up notes")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CLIENT RESPONSE SCHEMA
# ============================================================

class ClientResponse(ClientBase):
    """Schema for client response."""
    
    id: int = Field(..., description="Client ID")
    company_name: str = Field(..., description="Company name")
    trading_name: Optional[str] = Field(default=None, description="Trading name")
    
    client_type: str = Field(..., description="Client type")
    display_client_type: str = Field(..., description="Human-readable client type")
    industry: str = Field(..., description="Industry")
    display_industry: str = Field(..., description="Human-readable industry")
    
    email: str = Field(..., description="Primary email")
    phone: Optional[str] = Field(default=None, description="Phone number")
    alternate_phone: Optional[str] = Field(default=None, description="Alternate phone")
    website: Optional[str] = Field(default=None, description="Website URL")
    
    address: Dict[str, Optional[str]] = Field(..., description="Full address")
    
    registration_number: Optional[str] = Field(default=None, description="Registration number")
    tax_id: Optional[str] = Field(default=None, description="Tax ID")
    company_size: Optional[str] = Field(default=None, description="Company size")
    founded_year: Optional[int] = Field(default=None, description="Founded year")
    logo_url: Optional[str] = Field(default=None, description="Logo URL")
    
    status: str = Field(..., description="Client status")
    display_status: str = Field(..., description="Human-readable status")
    priority: int = Field(..., description="Priority (1=Normal, 2=High, 3=VIP)")
    is_vip: bool = Field(..., description="Is VIP client")
    
    referred_by: Optional[str] = Field(default=None, description="Referred by")
    referral_source: Optional[str] = Field(default=None, description="Referral source")
    
    assigned_to: Optional[int] = Field(default=None, description="Assigned to user ID")
    assigned_to_name: Optional[str] = Field(default=None, description="Assigned to user name")
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    project_count: int = Field(..., description="Total projects")
    active_project_count: int = Field(..., description="Active projects")
    total_revenue: float = Field(..., description="Total revenue")
    
    primary_contact: Optional[ClientContactResponse] = Field(
        default=None,
        description="Primary contact"
    )
    
    contacts: Optional[List[ClientContactResponse]] = Field(
        default=None,
        description="All contacts"
    )
    
    social_links: Optional[Dict[str, str]] = Field(
        default=None,
        description="Social media links"
    )
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# CLIENT DETAIL RESPONSE
# ============================================================

class ClientDetailResponse(ClientResponse):
    """Schema for client detail response with full information."""
    
    billing_address: Optional[str] = Field(default=None, description="Billing address")
    billing_email: Optional[str] = Field(default=None, description="Billing email")
    billing_phone: Optional[str] = Field(default=None, description="Billing phone")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    credit_limit: Optional[float] = Field(default=None, description="Credit limit")
    
    communications: Optional[List[ClientCommunicationResponse]] = Field(
        default=None,
        description="Communications"
    )
    
    projects: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Projects"
    )


# ============================================================
# CLIENT LIST REQUEST (Filters)
# ============================================================

class ClientListRequest(ClientBase):
    """Schema for client list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by company name or email")
    status: Optional[ClientStatusEnum] = Field(default=None, description="Filter by status")
    industry: Optional[ClientIndustryEnum] = Field(default=None, description="Filter by industry")
    client_type: Optional[ClientTypeEnum] = Field(default=None, description="Filter by client type")
    assigned_to: Optional[int] = Field(default=None, description="Filter by assigned user")
    priority: Optional[int] = Field(default=None, ge=1, le=3, description="Filter by priority")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# CLIENT LIST RESPONSE
# ============================================================

class ClientListResponse(ClientBase):
    """Schema for paginated client list response."""
    
    clients: List[ClientResponse] = Field(..., description="List of clients")
    total: int = Field(..., description="Total clients")
    active_count: int = Field(..., description="Active clients")
    lead_count: int = Field(..., description="Lead clients")
    prospect_count: int = Field(..., description="Prospect clients")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# CLIENT STATISTICS (Admin View)
# ============================================================

class ClientStatistics(ClientBase):
    """Schema for client statistics."""
    
    total_clients: int = Field(..., description="Total clients")
    active: int = Field(..., description="Active clients")
    inactive: int = Field(..., description="Inactive clients")
    leads: int = Field(..., description="Lead clients")
    prospects: int = Field(..., description="Prospect clients")
    former: int = Field(..., description="Former clients")
    blacklisted: int = Field(..., description="Blacklisted clients")
    
    # NEW: Priority breakdown
    vip_clients: int = Field(..., description="VIP clients")
    high_priority: int = Field(..., description="High priority clients")
    normal_priority: int = Field(..., description="Normal priority clients")
    
    # NEW: Industry breakdown
    industry_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Clients by industry"
    )
    
    # NEW: Type breakdown
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Clients by type"
    )
    
    # NEW: Revenue stats
    total_revenue: float = Field(..., description="Total revenue")
    average_revenue_per_client: float = Field(..., description="Average revenue per client")
    
    # NEW: Top clients
    top_clients: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top revenue clients"
    )
    
    # NEW: Daily trends
    daily_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily client trends"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ClientStatusEnum",
    "ClientTypeEnum",
    "ClientIndustryEnum",
    "ContactRoleEnum",
    "ClientCreate",
    "ClientUpdate",
    "ClientContactCreate",
    "ClientContactUpdate",
    "ClientContactResponse",
    "ClientCommunicationCreate",
    "ClientCommunicationUpdate",
    "ClientCommunicationResponse",
    "ClientResponse",
    "ClientDetailResponse",
    "ClientListRequest",
    "ClientListResponse",
    "ClientStatistics",
]