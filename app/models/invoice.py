# ============================================================
# AETHER LINK - INVOICE MODEL (Software House)
# ============================================================
# Purpose: Manage client invoices, billing, and payment tracking
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class InvoiceStatus(str, enum.Enum):
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


class InvoiceType(str, enum.Enum):
    """Invoice type enumeration."""
    PROJECT = "project"
    RETAINER = "retainer"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"


class InvoicePaymentMethod(str, enum.Enum):
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
# 1. INVOICE MODEL
# ============================================================

class Invoice(Base):
    __tablename__ = "invoices"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("client_projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # INVOICE DETAILS
    # ============================================================
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    invoice_type = Column(
        String(50),
        default=InvoiceType.PROJECT.value,
        nullable=False
    )
    
    # NEW: External reference (PO number, etc.)
    reference_number = Column(String(100), nullable=True)
    
    # ============================================================
    # DATES
    # ============================================================
    issue_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: Period (for recurring invoices)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # FINANCIALS
    # ============================================================
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    tax_rate = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    tax_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    discount_type = Column(String(20), nullable=True)  # percentage, fixed
    discount_value = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    discount_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    shipping_cost = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # NEW: Currency
    currency = Column(String(3), default="PKR", nullable=False)
    
    # ============================================================
    # PAYMENT TRACKING
    # ============================================================
    amount_paid = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    amount_due = Column(DECIMAL(12, 2), nullable=False)
    
    payment_method = Column(
        String(50),
        nullable=True
    )
    
    # NEW: Payment reference (transaction ID)
    payment_reference = Column(String(255), nullable=True)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=InvoiceStatus.DRAFT.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # RECURRING
    # ============================================================
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_interval = Column(String(50), nullable=True)  # monthly, quarterly, yearly
    recurring_end_date = Column(DateTime(timezone=True), nullable=True)
    recurring_next_date = Column(DateTime(timezone=True), nullable=True)
    recurring_parent_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # NEW: NOTES
    # ============================================================
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    footer_notes = Column(Text, nullable=True)
    
    # ============================================================
    # NEW: CREATOR
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Sent by
    sent_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # ============================================================
    # NEW: ATTACHMENTS
    # ============================================================
    attachments = Column(JSON, nullable=True)
    
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
        Index('ix_invoices_client', 'client_id'),
        Index('ix_invoices_project', 'project_id'),
        Index('ix_invoices_status', 'status'),
        Index('ix_invoices_due_date', 'due_date'),
        Index('ix_invoices_issue_date', 'issue_date'),
        Index('ix_invoices_created_by', 'created_by'),
        Index('ix_invoices_number', 'invoice_number'),
        Index('ix_invoices_recurring_parent', 'recurring_parent_id'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    client = relationship(
        "Client",
        back_populates="invoices",
        foreign_keys=[client_id]
    )
    
    project = relationship(
        "ClientProject",
        back_populates="invoices",
        foreign_keys=[project_id]
    )
    
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        uselist=False
    )
    
    sent_by_user = relationship(
        "User",
        foreign_keys=[sent_by],
        uselist=False
    )
    
    # NEW: Invoice items
    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    # NEW: Recurring parent/children
    recurring_parent = relationship(
        "Invoice",
        remote_side=[id],
        foreign_keys=[recurring_parent_id],
        uselist=False
    )
    
    recurring_children = relationship(
        "Invoice",
        foreign_keys=[recurring_parent_id],
        cascade="all, delete-orphan"
    )
    
    # NEW: Payment records
    payments = relationship(
        "InvoicePayment",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Invoice {self.id}: {self.invoice_number}>"
    
    def __str__(self) -> str:
        return f"{self.invoice_number} - {self.client.company_name if self.client else 'Unknown Client'}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_draft_invoice(self) -> bool:
        """Check if invoice is draft."""
        return self.status == InvoiceStatus.DRAFT.value
    
    @property
    def is_sent_invoice(self) -> bool:
        """Check if invoice is sent."""
        return self.status == InvoiceStatus.SENT.value
    
    @property
    def is_paid_invoice(self) -> bool:
        """Check if invoice is paid."""
        return self.status == InvoiceStatus.PAID.value
    
    @property
    def is_overdue_invoice(self) -> bool:
        """Check if invoice is overdue."""
        return self.status == InvoiceStatus.OVERDUE.value
    
    @property
    def is_cancelled_invoice(self) -> bool:
        """Check if invoice is cancelled."""
        return self.status == InvoiceStatus.CANCELLED.value
    
    @property
    def is_refunded_invoice(self) -> bool:
        """Check if invoice is refunded."""
        return self.status == InvoiceStatus.REFUNDED.value
    
    @property
    def is_partially_paid(self) -> bool:
        """Check if invoice is partially paid."""
        return self.status == InvoiceStatus.PARTIALLY_PAID.value
    
    @property
    def is_viewed(self) -> bool:
        """Check if invoice has been viewed."""
        return self.status == InvoiceStatus.VIEWED.value or self.viewed_at is not None
    
    @property
    def is_fully_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.amount_due <= 0 and self.status == InvoiceStatus.PAID.value
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.is_paid_invoice or self.is_cancelled_invoice or self.is_refunded_invoice:
            return False
        return self.due_date < func.now()
    
    @property
    def days_until_due(self) -> int:
        """Get days until invoice due date."""
        if self.due_date is None:
            return -1
        delta = self.due_date - func.now()
        return max(0, delta.days)
    
    @property
    def days_overdue(self) -> int:
        """Get days overdue."""
        if not self.is_overdue:
            return 0
        delta = func.now() - self.due_date
        return delta.days
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        status_map = {
            "draft": "📝 Draft",
            "sent": "📤 Sent",
            "viewed": "👁️ Viewed",
            "partially_paid": "💰 Partially Paid",
            "paid": "✅ Paid",
            "overdue": "⚠️ Overdue",
            "cancelled": "❌ Cancelled",
            "refunded": "↩️ Refunded",
            "written_off": "✏️ Written Off",
        }
        return status_map.get(self.status, "Unknown")
    
    @property
    def display_type(self) -> str:
        """Get human-readable invoice type."""
        type_map = {
            "project": "📋 Project",
            "retainer": "🔄 Retainer",
            "one_time": "💳 One-Time",
            "recurring": "🔄 Recurring",
            "credit_note": "📝 Credit Note",
            "debit_note": "📝 Debit Note",
        }
        return type_map.get(self.invoice_type, "Project")
    
    @property
    def balance_remaining(self) -> float:
        """Get remaining balance."""
        return float(self.total_amount) - float(self.amount_paid)
    
    @property
    def payment_percentage(self) -> float:
        """Calculate payment percentage."""
        if self.total_amount == 0:
            return 0.0
        return (float(self.amount_paid) / float(self.total_amount)) * 100
    
    @property
    def total_items(self) -> int:
        """Get total number of items."""
        return len(self.items) if self.items else 0
    
    @property
    def is_over_budget(self) -> bool:
        """Check if invoice exceeds project budget."""
        if not self.project or not self.project.budget:
            return False
        return float(self.total_amount) > float(self.project.budget)
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def send_invoice(self, sent_by: int) -> None:
        """Send the invoice."""
        self.status = InvoiceStatus.SENT.value
        self.sent_at = func.now()
        self.sent_by = sent_by
    
    def mark_viewed(self) -> None:
        """Mark invoice as viewed."""
        self.status = InvoiceStatus.VIEWED.value
        self.viewed_at = func.now()
    
    def record_payment(self, amount: float, method: str, reference: str = None) -> None:
        """
        Record a payment on the invoice.
        
        Args:
            amount: Amount paid
            method: Payment method
            reference: Payment reference/transaction ID
        """
        self.amount_paid += amount
        self.amount_due = float(self.total_amount) - float(self.amount_paid)
        
        if self.amount_due <= 0:
            self.status = InvoiceStatus.PAID.value
            self.paid_at = func.now()
        else:
            self.status = InvoiceStatus.PARTIALLY_PAID.value
        
        self.payment_method = method
        if reference:
            self.payment_reference = reference
        
        # Create payment record
        payment = InvoicePayment(
            amount=amount,
            method=method,
            reference=reference
        )
        if self.payments is None:
            self.payments = []
        self.payments.append(payment)
    
    def void_invoice(self) -> None:
        """Void/cancel the invoice."""
        self.status = InvoiceStatus.CANCELLED.value
    
    def refund_invoice(self) -> None:
        """Refund the invoice."""
        self.status = InvoiceStatus.REFUNDED.value
        self.amount_paid = 0
        self.amount_due = float(self.total_amount)
    
    def write_off(self) -> None:
        """Write off the invoice."""
        self.status = InvoiceStatus.WRITTEN_OFF.value
        self.amount_due = 0
    
    def mark_overdue(self) -> None:
        """Mark invoice as overdue."""
        if self.is_overdue and self.status not in [InvoiceStatus.PAID.value, InvoiceStatus.CANCELLED.value]:
            self.status = InvoiceStatus.OVERDUE.value
    
    def set_recurring(self, interval: str, end_date: DateTime = None) -> None:
        """Set invoice as recurring."""
        self.is_recurring = True
        self.recurring_interval = interval
        self.recurring_end_date = end_date
        self.recurring_next_date = self.calculate_next_date()
    
    def calculate_next_date(self) -> DateTime:
        """Calculate next recurring date."""
        if not self.is_recurring or not self.issue_date:
            return None
        
        if self.recurring_interval == "monthly":
            return self.issue_date + func.interval('1 month')
        elif self.recurring_interval == "quarterly":
            return self.issue_date + func.interval('3 months')
        elif self.recurring_interval == "yearly":
            return self.issue_date + func.interval('1 year')
        return None
    
    def add_item(self, description: str, quantity: int, unit_price: float, tax_rate: float = None) -> 'InvoiceItem':
        """Add an item to the invoice."""
        item = InvoiceItem(
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=tax_rate
        )
        if self.items is None:
            self.items = []
        self.items.append(item)
        self.recalculate_totals()
        return item
    
    def recalculate_totals(self) -> None:
        """Recalculate all invoice totals."""
        if not self.items:
            self.subtotal = 0
            self.tax_amount = 0
            self.total_amount = 0
            return
        
        # Calculate subtotal
        subtotal = sum(float(item.total_price) for item in self.items)
        self.subtotal = subtotal
        
        # Calculate tax
        tax_amount = 0
        for item in self.items:
            if item.tax_rate:
                tax_amount += float(item.total_price) * (float(item.tax_rate) / 100)
        self.tax_amount = tax_amount
        
        # Calculate discount
        if self.discount_type == "percentage":
            self.discount_amount = (subtotal + tax_amount) * (float(self.discount_value) / 100)
        else:  # fixed
            self.discount_amount = float(self.discount_value)
        
        # Calculate total
        total = subtotal + tax_amount + float(self.shipping_cost) - self.discount_amount
        self.total_amount = total
        
        # Update amount due
        self.amount_due = total - float(self.amount_paid)
        
        # Update status if fully paid
        if self.amount_due <= 0 and self.status != InvoiceStatus.PAID.value:
            self.status = InvoiceStatus.PAID.value
    
    def soft_delete_invoice(self) -> None:
        """Soft delete the invoice."""
        self.deleted_at = func.now()
    
    def restore_invoice(self) -> None:
        """Restore a soft-deleted invoice."""
        self.deleted_at = None
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata JSON field."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @staticmethod
    def validate_invoice_number(number: str) -> bool:
        """Validate invoice number format."""
        import re
        return bool(re.match(r'^INV-[0-9]{4}-[0-9]{6,}$', number))
    
    @staticmethod
    def validate_tax_rate(rate: float) -> bool:
        """Validate tax rate."""
        return 0 <= rate <= 100
    
    @staticmethod
    def validate_discount_value(value: float, discount_type: str) -> bool:
        """Validate discount value."""
        if discount_type == "percentage":
            return 0 <= value <= 100
        return value >= 0
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert invoice to dictionary."""
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client.company_name if self.client else None,
            "project_id": self.project_id,
            "project_name": self.project.name if self.project else None,
            "invoice_number": self.invoice_number,
            "invoice_type": self.invoice_type,
            "display_type": self.display_type,
            "reference_number": self.reference_number,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
            "is_viewed": self.is_viewed,
            "subtotal": float(self.subtotal),
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0.0,
            "tax_amount": float(self.tax_amount),
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value) if self.discount_value else 0.0,
            "discount_amount": float(self.discount_amount),
            "shipping_cost": float(self.shipping_cost),
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "amount_paid": float(self.amount_paid),
            "amount_due": float(self.amount_due),
            "balance_remaining": self.balance_remaining,
            "payment_percentage": self.payment_percentage,
            "is_fully_paid": self.is_fully_paid,
            "status": self.status,
            "display_status": self.display_status,
            "is_overdue": self.is_overdue,
            "days_until_due": self.days_until_due,
            "days_overdue": self.days_overdue,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "is_recurring": self.is_recurring,
            "recurring_interval": self.recurring_interval,
            "recurring_end_date": self.recurring_end_date.isoformat() if self.recurring_end_date else None,
            "recurring_next_date": self.recurring_next_date.isoformat() if self.recurring_next_date else None,
            "notes": self.notes,
            "terms_and_conditions": self.terms_and_conditions,
            "footer_notes": self.footer_notes,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "total_items": self.total_items,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "payments": [payment.to_dict() for payment in self.payments] if self.payments else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "period_start": self.period_start.isoformat() if self.period_start else None,
                "period_end": self.period_end.isoformat() if self.period_end else None,
                "sent_by": self.sent_by,
                "sent_by_name": self.sent_by_user.full_name if self.sent_by_user else None,
                "recurring_parent_id": self.recurring_parent_id,
                "attachments": self.attachments,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing invoice data."""
        data = self.to_dict()
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing invoice data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. INVOICE ITEM MODEL
# ============================================================

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Item details
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    total_price = Column(DECIMAL(12, 2), nullable=False)
    
    # NEW: Tax
    tax_rate = Column(DECIMAL(5, 2), nullable=True)
    tax_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    
    # NEW: Discount
    discount_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    
    # NEW: Reference
    reference_id = Column(Integer, nullable=True)  # Task ID, Project ID, etc.
    reference_type = Column(String(50), nullable=True)  # task, project, timesheet
    
    # NEW: Metadata
    metadata = Column(JSON, nullable=True)
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_invoice_items_invoice', 'invoice_id'),
        Index('ix_invoice_items_reference', 'reference_id', 'reference_type'),
    )
    
    # RELATIONSHIPS
    invoice = relationship(
        "Invoice",
        back_populates="items",
        foreign_keys=[invoice_id]
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceItem {self.id}: {self.description[:30]}...>"
    
    @property
    def total_price_display(self) -> float:
        """Get total price with tax."""
        return float(self.total_price) + float(self.tax_amount or 0) - float(self.discount_amount or 0)
    
    @property
    def display_tax_rate(self) -> str:
        """Get display tax rate."""
        if self.tax_rate is None:
            return "N/A"
        return f"{self.tax_rate}%"
    
    def calculate_totals(self) -> None:
        """Calculate item totals."""
        self.total_price = self.quantity * self.unit_price
        if self.tax_rate:
            self.tax_amount = self.total_price * (self.tax_rate / 100)
        else:
            self.tax_amount = 0
    
    def to_dict(self) -> dict:
        """Convert invoice item to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
            "tax_rate": float(self.tax_rate) if self.tax_rate else None,
            "tax_amount": float(self.tax_amount),
            "discount_amount": float(self.discount_amount),
            "final_price": self.total_price_display,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# 3. INVOICE PAYMENT MODEL
# ============================================================

class InvoicePayment(Base):
    __tablename__ = "invoice_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # NEW: Payment details
    amount = Column(DECIMAL(12, 2), nullable=False)
    method = Column(
        String(50),
        nullable=False
    )
    
    # NEW: Payment reference
    reference = Column(String(255), nullable=True)
    
    # NEW: Payment date
    payment_date = Column(DateTime(timezone=True), nullable=False)
    
    # NEW: Received by
    received_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Status
    status = Column(String(20), default="completed", nullable=False)  # pending, completed, failed, refunded
    
    # NEW: Metadata
    metadata = Column(JSON, nullable=True)
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_invoice_payments_invoice', 'invoice_id'),
        Index('ix_invoice_payments_received_by', 'received_by'),
        Index('ix_invoice_payments_payment_date', 'payment_date'),
        Index('ix_invoice_payments_status', 'status'),
    )
    
    # RELATIONSHIPS
    invoice = relationship(
        "Invoice",
        back_populates="payments",
        foreign_keys=[invoice_id]
    )
    
    received_by_user = relationship(
        "User",
        foreign_keys=[received_by],
        uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<InvoicePayment {self.id}: {self.amount} - {self.method}>"
    
    def to_dict(self) -> dict:
        """Convert invoice payment to dictionary."""
        return {
            "id": self.id,
            "amount": float(self.amount),
            "method": self.method,
            "reference": self.reference,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "received_by": self.received_by,
            "received_by_name": self.received_by_user.full_name if self.received_by_user else None,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# 4. INVOICE SETTINGS
# ============================================================

class InvoiceSettings(Base):
    """System-wide invoice settings."""
    __tablename__ = "invoice_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # NEW: Company info
    company_name = Column(String(255), nullable=True)
    company_address = Column(Text, nullable=True)
    company_phone = Column(String(50), nullable=True)
    company_email = Column(String(255), nullable=True)
    company_website = Column(String(255), nullable=True)
    company_logo_url = Column(String(500), nullable=True)
    
    # NEW: Tax info
    tax_registration_number = Column(String(100), nullable=True)
    default_tax_rate = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    
    # NEW: Default invoice settings
    default_currency = Column(String(3), default="PKR", nullable=False)
    default_terms = Column(Text, nullable=True)
    default_footer = Column(Text, nullable=True)
    
    # NEW: Payment methods
    payment_methods = Column(JSON, nullable=True)  # ["bank_transfer", "easypaisa", "jazzcash"]
    
    # NEW: Invoice numbering
    invoice_prefix = Column(String(10), default="INV-", nullable=False)
    invoice_starting_number = Column(Integer, default=1000, nullable=False)
    
    # NEW: Next invoice number
    next_invoice_number = Column(Integer, nullable=True)
    
    # NEW: Bank details
    bank_name = Column(String(255), nullable=True)
    bank_account_number = Column(String(100), nullable=True)
    bank_iban = Column(String(100), nullable=True)
    bank_swift = Column(String(20), nullable=True)
    
    # NEW: EasyPaisa/JazzCash details
    easypaisa_account = Column(String(50), nullable=True)
    jazzcash_account = Column(String(50), nullable=True)
    
    # NEW: Updated by
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # NEW: Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # CONSTRAINTS
    __table_args__ = (
        Index('ix_invoice_settings_company', 'company_name'),
    )
    
    # RELATIONSHIPS
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self) -> str:
        return f"<InvoiceSettings {self.id}>"
    
    def get_next_invoice_number(self) -> str:
        """Generate the next invoice number."""
        if self.next_invoice_number is None:
            self.next_invoice_number = self.invoice_starting_number
        
        number = self.next_invoice_number
        self.next_invoice_number += 1
        return f"{self.invoice_prefix}{number}"
    
    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "company_address": self.company_address,
            "company_phone": self.company_phone,
            "company_email": self.company_email,
            "company_website": self.company_website,
            "company_logo_url": self.company_logo_url,
            "tax_registration_number": self.tax_registration_number,
            "default_tax_rate": float(self.default_tax_rate) if self.default_tax_rate else 0.0,
            "default_currency": self.default_currency,
            "default_terms": self.default_terms,
            "default_footer": self.default_footer,
            "payment_methods": self.payment_methods,
            "invoice_prefix": self.invoice_prefix,
            "next_invoice_number": self.next_invoice_number,
            "bank_name": self.bank_name,
            "bank_account_number": self.bank_account_number,
            "bank_iban": self.bank_iban,
            "bank_swift": self.bank_swift,
            "easypaisa_account": self.easypaisa_account,
            "jazzcash_account": self.jazzcash_account,
        }