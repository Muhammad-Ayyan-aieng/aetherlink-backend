# ============================================================
# AETHER LINK - INVOICE SCHEMAS (Software House)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ============================================================
# INVOICE ENUMS
# ============================================================

class InvoiceStatusEnum(str, Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    WRITTEN_OFF = "written_off"


class InvoiceTypeEnum(str, Enum):
    """Invoice type enumeration."""
    PROJECT = "project"
    RETAINER = "retainer"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"


class InvoicePaymentMethodEnum(str, Enum):
    """Invoice payment method enumeration."""
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CASH = "cash"
    CHEQUE = "cheque"
    OTHER = "other"


# ============================================================
# BASE SCHEMA
# ============================================================

class InvoiceBase(BaseModel):
    """Base invoice schema."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )


# ============================================================
# INVOICE CREATE SCHEMA
# ============================================================

class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    
    client_id: int = Field(..., gt=0, description="Client ID")
    project_id: Optional[int] = Field(default=None, gt=0, description="Project ID")
    
    invoice_type: InvoiceTypeEnum = Field(
        default=InvoiceTypeEnum.PROJECT,
        description="Invoice type"
    )
    reference_number: Optional[str] = Field(default=None, max_length=100, description="Reference/PO number")
    
    issue_date: date = Field(..., description="Issue date")
    due_date: date = Field(..., description="Due date")
    
    # NEW: Period (for recurring invoices)
    period_start: Optional[date] = Field(default=None, description="Period start")
    period_end: Optional[date] = Field(default=None, description="Period end")
    
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="Tax rate percentage")
    discount_type: Optional[str] = Field(default=None, max_length=20, description="Discount type (percentage, fixed)")
    discount_value: float = Field(default=0.0, ge=0, description="Discount value")
    shipping_cost: float = Field(default=0.0, ge=0, description="Shipping cost")
    
    currency: str = Field(default="PKR", max_length=3, description="Currency code")
    
    notes: Optional[str] = Field(default=None, max_length=500, description="Invoice notes")
    terms_and_conditions: Optional[str] = Field(default=None, max_length=1000, description="Terms and conditions")
    footer_notes: Optional[str] = Field(default=None, max_length=500, description="Footer notes")
    
    # NEW: Recurring settings
    is_recurring: bool = Field(default=False, description="Is recurring invoice")
    recurring_interval: Optional[str] = Field(default=None, max_length=50, description="Recurring interval")
    recurring_end_date: Optional[date] = Field(default=None, description="Recurring end date")
    
    # NEW: Items
    items: List['InvoiceItemCreate'] = Field(..., min_length=1, description="Invoice items")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: date, info: Dict[str, Any]) -> date:
        """Validate due date is after issue date."""
        data = info.data
        if 'issue_date' in data and data['issue_date']:
            if v <= data['issue_date']:
                raise ValueError('Due date must be after issue date')
        return v


# ============================================================
# INVOICE ITEM CREATE SCHEMA
# ============================================================

class InvoiceItemCreate(InvoiceBase):
    """Schema for creating an invoice item."""
    
    description: str = Field(..., min_length=1, max_length=500, description="Item description")
    quantity: int = Field(default=1, ge=1, description="Quantity")
    unit_price: float = Field(..., gt=0, description="Unit price")
    
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Tax rate for this item")
    discount_amount: float = Field(default=0.0, ge=0, description="Discount amount")
    
    reference_id: Optional[int] = Field(default=None, description="Reference ID (task, timesheet, etc.)")
    reference_type: Optional[str] = Field(default=None, max_length=50, description="Reference type")


class InvoiceItemUpdate(InvoiceBase):
    """Schema for updating an invoice item."""
    
    description: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Item description")
    quantity: Optional[int] = Field(default=None, ge=1, description="Quantity")
    unit_price: Optional[float] = Field(default=None, gt=0, description="Unit price")
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Tax rate")
    discount_amount: Optional[float] = Field(default=None, ge=0, description="Discount amount")
    reference_id: Optional[int] = Field(default=None, description="Reference ID")
    reference_type: Optional[str] = Field(default=None, max_length=50, description="Reference type")


class InvoiceItemResponse(InvoiceBase):
    """Schema for invoice item response."""
    
    id: int = Field(..., description="Item ID")
    invoice_id: int = Field(..., description="Invoice ID")
    
    description: str = Field(..., description="Item description")
    quantity: int = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    total_price: float = Field(..., description="Total price")
    
    tax_rate: Optional[float] = Field(default=None, description="Tax rate")
    tax_amount: float = Field(..., description="Tax amount")
    discount_amount: float = Field(..., description="Discount amount")
    final_price: float = Field(..., description="Final price (with tax and discount)")
    
    reference_id: Optional[int] = Field(default=None, description="Reference ID")
    reference_type: Optional[str] = Field(default=None, description="Reference type")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# INVOICE UPDATE SCHEMA
# ============================================================

class InvoiceUpdate(InvoiceBase):
    """Schema for updating an invoice."""
    
    invoice_type: Optional[InvoiceTypeEnum] = Field(default=None, description="Invoice type")
    reference_number: Optional[str] = Field(default=None, max_length=100, description="Reference number")
    
    due_date: Optional[date] = Field(default=None, description="Due date")
    
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Tax rate")
    discount_type: Optional[str] = Field(default=None, max_length=20, description="Discount type")
    discount_value: Optional[float] = Field(default=None, ge=0, description="Discount value")
    shipping_cost: Optional[float] = Field(default=None, ge=0, description="Shipping cost")
    
    notes: Optional[str] = Field(default=None, max_length=500, description="Invoice notes")
    terms_and_conditions: Optional[str] = Field(default=None, max_length=1000, description="Terms and conditions")
    footer_notes: Optional[str] = Field(default=None, max_length=500, description="Footer notes")
    
    status: Optional[InvoiceStatusEnum] = Field(default=None, description="Invoice status")


# ============================================================
# INVOICE PAYMENT SCHEMAS
# ============================================================

class InvoicePaymentCreate(InvoiceBase):
    """Schema for recording an invoice payment."""
    
    invoice_id: int = Field(..., gt=0, description="Invoice ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    method: InvoicePaymentMethodEnum = Field(..., description="Payment method")
    reference: Optional[str] = Field(default=None, max_length=255, description="Payment reference/transaction ID")
    payment_date: date = Field(..., description="Payment date")
    notes: Optional[str] = Field(default=None, max_length=500, description="Payment notes")


class InvoicePaymentResponse(InvoiceBase):
    """Schema for invoice payment response."""
    
    id: int = Field(..., description="Payment ID")
    invoice_id: int = Field(..., description="Invoice ID")
    
    amount: float = Field(..., description="Payment amount")
    method: str = Field(..., description="Payment method")
    reference: Optional[str] = Field(default=None, description="Payment reference")
    payment_date: date = Field(..., description="Payment date")
    notes: Optional[str] = Field(default=None, description="Payment notes")
    
    received_by: Optional[int] = Field(default=None, description="Received by user ID")
    received_by_name: Optional[str] = Field(default=None, description="Received by user name")
    
    status: str = Field(..., description="Payment status")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# INVOICE RESPONSE SCHEMA
# ============================================================

class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    
    id: int = Field(..., description="Invoice ID")
    client_id: int = Field(..., description="Client ID")
    client_name: Optional[str] = Field(default=None, description="Client name")
    project_id: Optional[int] = Field(default=None, description="Project ID")
    project_name: Optional[str] = Field(default=None, description="Project name")
    
    invoice_number: str = Field(..., description="Invoice number")
    invoice_type: str = Field(..., description="Invoice type")
    display_type: str = Field(..., description="Human-readable type")
    reference_number: Optional[str] = Field(default=None, description="Reference number")
    
    issue_date: date = Field(..., description="Issue date")
    due_date: date = Field(..., description="Due date")
    paid_at: Optional[datetime] = Field(default=None, description="Paid timestamp")
    sent_at: Optional[datetime] = Field(default=None, description="Sent timestamp")
    viewed_at: Optional[datetime] = Field(default=None, description="Viewed timestamp")
    is_viewed: bool = Field(..., description="Is viewed")
    
    subtotal: float = Field(..., description="Subtotal")
    tax_rate: float = Field(..., description="Tax rate")
    tax_amount: float = Field(..., description="Tax amount")
    discount_type: Optional[str] = Field(default=None, description="Discount type")
    discount_value: float = Field(..., description="Discount value")
    discount_amount: float = Field(..., description="Discount amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    total_amount: float = Field(..., description="Total amount")
    
    currency: str = Field(..., description="Currency code")
    
    amount_paid: float = Field(..., description="Amount paid")
    amount_due: float = Field(..., description="Amount due")
    balance_remaining: float = Field(..., description="Balance remaining")
    payment_percentage: float = Field(..., description="Payment percentage")
    is_fully_paid: bool = Field(..., description="Is fully paid")
    
    status: str = Field(..., description="Invoice status")
    display_status: str = Field(..., description="Human-readable status")
    is_overdue: bool = Field(..., description="Is overdue")
    days_until_due: int = Field(..., description="Days until due")
    days_overdue: int = Field(..., description="Days overdue")
    
    payment_method: Optional[str] = Field(default=None, description="Payment method")
    payment_reference: Optional[str] = Field(default=None, description="Payment reference")
    
    is_recurring: bool = Field(..., description="Is recurring")
    recurring_interval: Optional[str] = Field(default=None, description="Recurring interval")
    recurring_end_date: Optional[date] = Field(default=None, description="Recurring end date")
    recurring_next_date: Optional[date] = Field(default=None, description="Recurring next date")
    recurring_parent_id: Optional[int] = Field(default=None, description="Recurring parent ID")
    
    notes: Optional[str] = Field(default=None, description="Invoice notes")
    terms_and_conditions: Optional[str] = Field(default=None, description="Terms and conditions")
    footer_notes: Optional[str] = Field(default=None, description="Footer notes")
    
    created_by: Optional[int] = Field(default=None, description="Created by user ID")
    created_by_name: Optional[str] = Field(default=None, description="Created by user name")
    
    total_items: int = Field(..., description="Total items")
    items: List[InvoiceItemResponse] = Field(..., description="Invoice items")
    payments: List[InvoicePaymentResponse] = Field(default_factory=list, description="Payments")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ============================================================
# INVOICE DETAIL RESPONSE
# ============================================================

class InvoiceDetailResponse(InvoiceResponse):
    """Schema for invoice detail response."""
    
    # NEW: Client details
    client_email: Optional[str] = Field(default=None, description="Client email")
    client_phone: Optional[str] = Field(default=None, description="Client phone")
    client_address: Optional[str] = Field(default=None, description="Client address")
    
    # NEW: Project details
    project_description: Optional[str] = Field(default=None, description="Project description")
    
    # NEW: Company details (from settings)
    company_name: Optional[str] = Field(default=None, description="Company name")
    company_address: Optional[str] = Field(default=None, description="Company address")
    company_phone: Optional[str] = Field(default=None, description="Company phone")
    company_email: Optional[str] = Field(default=None, description="Company email")
    company_logo_url: Optional[str] = Field(default=None, description="Company logo URL")
    
    # NEW: Bank details
    bank_name: Optional[str] = Field(default=None, description="Bank name")
    bank_account_number: Optional[str] = Field(default=None, description="Bank account number")
    bank_iban: Optional[str] = Field(default=None, description="Bank IBAN")
    bank_swift: Optional[str] = Field(default=None, description="Bank SWIFT code")


# ============================================================
# INVOICE LIST REQUEST (Filters)
# ============================================================

class InvoiceListRequest(InvoiceBase):
    """Schema for invoice list request with filters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search by invoice number or client name")
    status: Optional[InvoiceStatusEnum] = Field(default=None, description="Filter by status")
    invoice_type: Optional[InvoiceTypeEnum] = Field(default=None, description="Filter by invoice type")
    client_id: Optional[int] = Field(default=None, description="Filter by client")
    project_id: Optional[int] = Field(default=None, description="Filter by project")
    is_recurring: Optional[bool] = Field(default=None, description="Filter by recurring")
    date_from: Optional[date] = Field(default=None, description="Filter from issue date")
    date_to: Optional[date] = Field(default=None, description="Filter to issue date")
    due_date_from: Optional[date] = Field(default=None, description="Filter from due date")
    due_date_to: Optional[date] = Field(default=None, description="Filter to due date")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


# ============================================================
# INVOICE LIST RESPONSE
# ============================================================

class InvoiceListResponse(InvoiceBase):
    """Schema for paginated invoice list response."""
    
    invoices: List[InvoiceResponse] = Field(..., description="List of invoices")
    total: int = Field(..., description="Total invoices")
    draft_count: int = Field(..., description="Draft invoices")
    sent_count: int = Field(..., description="Sent invoices")
    paid_count: int = Field(..., description="Paid invoices")
    overdue_count: int = Field(..., description="Overdue invoices")
    total_revenue: float = Field(..., description="Total revenue")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============================================================
# INVOICE STATISTICS (Admin View)
# ============================================================

class InvoiceStatistics(InvoiceBase):
    """Schema for invoice statistics."""
    
    total_invoices: int = Field(..., description="Total invoices")
    draft: int = Field(..., description="Draft invoices")
    sent: int = Field(..., description="Sent invoices")
    viewed: int = Field(..., description="Viewed invoices")
    partially_paid: int = Field(..., description="Partially paid invoices")
    paid: int = Field(..., description="Paid invoices")
    overdue: int = Field(..., description="Overdue invoices")
    cancelled: int = Field(..., description="Cancelled invoices")
    refunded: int = Field(..., description="Refunded invoices")
    written_off: int = Field(..., description="Written off invoices")
    
    # NEW: Revenue stats
    total_amount: float = Field(..., description="Total invoice amount")
    total_paid: float = Field(..., description="Total paid amount")
    total_due: float = Field(..., description="Total due amount")
    total_overdue: float = Field(..., description="Total overdue amount")
    collection_rate: float = Field(..., description="Collection rate percentage")
    
    # NEW: By type
    type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Invoices by type"
    )
    
    # NEW: By client
    top_clients: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top clients by revenue"
    )
    
    # NEW: Monthly trends
    monthly_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Monthly invoice trends"
    )


# ============================================================
# INVOICE BULK OPERATIONS
# ============================================================

class InvoiceBulkAction(InvoiceBase):
    """Schema for bulk invoice actions."""
    
    invoice_ids: List[int] = Field(..., min_length=1, description="List of invoice IDs")
    action: str = Field(..., description="Action to perform (send, cancel, delete)")
    note: Optional[str] = Field(default=None, max_length=500, description="Action note")


class InvoiceSendRequest(InvoiceBase):
    """Schema for sending invoices."""
    
    invoice_ids: List[int] = Field(..., min_length=1, description="List of invoice IDs")
    send_email: bool = Field(default=True, description="Send email notification")
    message: Optional[str] = Field(default=None, max_length=1000, description="Custom message")


class InvoiceSendResponse(InvoiceBase):
    """Schema for invoice send response."""
    
    sent_count: int = Field(..., description="Number of invoices sent")
    failed_count: int = Field(..., description="Number of invoices failed")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Error details")


# ============================================================
# INVOICE GENERATE FROM PROJECT
# ============================================================

class InvoiceGenerateFromProject(InvoiceBase):
    """Schema for generating an invoice from a project."""
    
    project_id: int = Field(..., gt=0, description="Project ID")
    issue_date: date = Field(..., description="Issue date")
    due_date: date = Field(..., description="Due date")
    
    # NEW: Include tasks
    include_tasks: List[int] = Field(default_factory=list, description="Task IDs to include")
    include_time_entries: bool = Field(default=True, description="Include time entries")
    time_entry_rate: Optional[float] = Field(default=None, gt=0, description="Rate for time entries")
    
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="Tax rate")
    discount_type: Optional[str] = Field(default=None, max_length=20, description="Discount type")
    discount_value: float = Field(default=0.0, ge=0, description="Discount value")
    
    notes: Optional[str] = Field(default=None, max_length=500, description="Invoice notes")
    terms_and_conditions: Optional[str] = Field(default=None, max_length=1000, description="Terms and conditions")


# ============================================================
# INVOICE SETTINGS SCHEMAS
# ============================================================

class InvoiceSettingsUpdate(InvoiceBase):
    """Schema for updating invoice settings."""
    
    company_name: Optional[str] = Field(default=None, max_length=255, description="Company name")
    company_address: Optional[str] = Field(default=None, max_length=500, description="Company address")
    company_phone: Optional[str] = Field(default=None, max_length=50, description="Company phone")
    company_email: Optional[EmailStr] = Field(default=None, description="Company email")
    company_website: Optional[str] = Field(default=None, max_length=255, description="Company website")
    company_logo_url: Optional[str] = Field(default=None, max_length=500, description="Company logo URL")
    
    tax_registration_number: Optional[str] = Field(default=None, max_length=100, description="Tax registration number")
    default_tax_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Default tax rate")
    
    default_currency: Optional[str] = Field(default=None, max_length=3, description="Default currency")
    default_terms: Optional[str] = Field(default=None, max_length=1000, description="Default terms")
    default_footer: Optional[str] = Field(default=None, max_length=500, description="Default footer")
    
    payment_methods: Optional[List[str]] = Field(default=None, description="Available payment methods")
    
    invoice_prefix: Optional[str] = Field(default=None, max_length=10, description="Invoice prefix")
    invoice_starting_number: Optional[int] = Field(default=None, ge=1, description="Starting invoice number")
    next_invoice_number: Optional[int] = Field(default=None, ge=1, description="Next invoice number")
    
    bank_name: Optional[str] = Field(default=None, max_length=255, description="Bank name")
    bank_account_number: Optional[str] = Field(default=None, max_length=100, description="Bank account number")
    bank_iban: Optional[str] = Field(default=None, max_length=100, description="Bank IBAN")
    bank_swift: Optional[str] = Field(default=None, max_length=20, description="Bank SWIFT code")
    
    easypaisa_account: Optional[str] = Field(default=None, max_length=50, description="EasyPaisa account")
    jazzcash_account: Optional[str] = Field(default=None, max_length=50, description="JazzCash account")


class InvoiceSettingsResponse(InvoiceBase):
    """Schema for invoice settings response."""
    
    company_name: Optional[str] = Field(default=None, description="Company name")
    company_address: Optional[str] = Field(default=None, description="Company address")
    company_phone: Optional[str] = Field(default=None, description="Company phone")
    company_email: Optional[str] = Field(default=None, description="Company email")
    company_website: Optional[str] = Field(default=None, description="Company website")
    company_logo_url: Optional[str] = Field(default=None, description="Company logo URL")
    
    tax_registration_number: Optional[str] = Field(default=None, description="Tax registration number")
    default_tax_rate: float = Field(..., description="Default tax rate")
    
    default_currency: str = Field(..., description="Default currency")
    default_terms: Optional[str] = Field(default=None, description="Default terms")
    default_footer: Optional[str] = Field(default=None, description="Default footer")
    
    payment_methods: List[str] = Field(..., description="Available payment methods")
    
    invoice_prefix: str = Field(..., description="Invoice prefix")
    next_invoice_number: int = Field(..., description="Next invoice number")
    
    bank_name: Optional[str] = Field(default=None, description="Bank name")
    bank_account_number: Optional[str] = Field(default=None, description="Bank account number")
    bank_iban: Optional[str] = Field(default=None, description="Bank IBAN")
    bank_swift: Optional[str] = Field(default=None, description="Bank SWIFT code")
    
    easypaisa_account: Optional[str] = Field(default=None, description="EasyPaisa account")
    jazzcash_account: Optional[str] = Field(default=None, description="JazzCash account")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "InvoiceStatusEnum",
    "InvoiceTypeEnum",
    "InvoicePaymentMethodEnum",
    "InvoiceCreate",
    "InvoiceItemCreate",
    "InvoiceItemUpdate",
    "InvoiceItemResponse",
    "InvoiceUpdate",
    "InvoicePaymentCreate",
    "InvoicePaymentResponse",
    "InvoiceResponse",
    "InvoiceDetailResponse",
    "InvoiceListRequest",
    "InvoiceListResponse",
    "InvoiceStatistics",
    "InvoiceBulkAction",
    "InvoiceSendRequest",
    "InvoiceSendResponse",
    "InvoiceGenerateFromProject",
    "InvoiceSettingsUpdate",
    "InvoiceSettingsResponse",
]