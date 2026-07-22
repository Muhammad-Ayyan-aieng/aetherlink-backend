# ============================================================
# AETHER LINK - COUPON MODEL
# ============================================================
# Purpose: Manage discount coupons for courses and learning paths
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class CouponType(str, enum.Enum):
    """Coupon type enumeration."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class CouponStatus(str, enum.Enum):
    """Coupon status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    DEPLETED = "depleted"
    DELETED = "deleted"


class CouponTargetType(str, enum.Enum):
    """Coupon target type enumeration."""
    COURSE = "course"
    LEARNING_PATH = "learning_path"
    ALL = "all"


class CouponUsageStatus(str, enum.Enum):
    """Coupon usage status enumeration."""
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ============================================================
# 1. COUPON MODEL
# ============================================================

class Coupon(Base):
    __tablename__ = "coupons"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # ============================================================
    # DISCOUNT SETTINGS
    # ============================================================
    discount_type = Column(
        String(20),
        default=CouponType.PERCENTAGE.value,
        nullable=False
    )
    discount_value = Column(DECIMAL(10, 2), nullable=False)
    
    # NEW: Maximum discount amount (for percentage coupons)
    max_discount_amount = Column(DECIMAL(10, 2), nullable=True)
    
    # NEW: Minimum purchase amount required
    min_purchase_amount = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    
    # ============================================================
    # TARGET
    # ============================================================
    target_type = Column(
        String(50),
        default=CouponTargetType.ALL.value,
        nullable=False
    )
    
    # NEW: Target specific course or learning path
    target_id = Column(Integer, nullable=True, index=True)
    
    # ============================================================
    # USAGE LIMITS
    # ============================================================
    usage_limit = Column(Integer, nullable=True)  # Max number of uses
    used_count = Column(Integer, default=0, nullable=False)
    
    # NEW: Per-user usage limit
    per_user_limit = Column(Integer, default=1, nullable=False)
    
    # NEW: First-time user only
    first_time_only = Column(Boolean, default=False, nullable=False)
    
    # ============================================================
    # DATES
    # ============================================================
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # NEW: Grace period (days after expiry for usage)
    grace_period_days = Column(Integer, default=0, nullable=False)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=CouponStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # NEW: CREATOR INFO
    # ============================================================
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
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
        Index('ix_coupons_status', 'status'),
        Index('ix_coupons_target_type', 'target_type'),
        Index('ix_coupons_start_date', 'start_date'),
        Index('ix_coupons_end_date', 'end_date'),
        Index('ix_coupons_created_by', 'created_by'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        uselist=False
    )
    
    usages = relationship(
        "CouponUsage",
        back_populates="coupon",
        cascade="all, delete-orphan"
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<Coupon {self.id}: {self.code}>"
    
    def __str__(self) -> str:
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == CouponType.PERCENTAGE.value else ' PKR'}"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_active(self) -> bool:
        """Check if coupon is active."""
        return (
            self.status == CouponStatus.ACTIVE.value
            and self.is_within_date_range
            and not self.is_usage_limit_reached
        )
    
    @property
    def is_inactive(self) -> bool:
        """Check if coupon is inactive."""
        return self.status == CouponStatus.INACTIVE.value
    
    @property
    def is_expired(self) -> bool:
        """Check if coupon is expired."""
        return self.status == CouponStatus.EXPIRED.value
    
    @property
    def is_depleted(self) -> bool:
        """Check if coupon is depleted."""
        return self.status == CouponStatus.DEPLETED.value
    
    @property
    def is_within_date_range(self) -> bool:
        """Check if current date is within coupon date range."""
        now = func.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def is_usage_limit_reached(self) -> bool:
        """Check if usage limit has been reached."""
        if self.usage_limit is None:
            return False
        return self.used_count >= self.usage_limit
    
    @property
    def remaining_uses(self) -> int:
        """Get remaining uses for the coupon."""
        if self.usage_limit is None:
            return -1  # Unlimited
        return max(0, self.usage_limit - self.used_count)
    
    @property
    def has_unlimited_uses(self) -> bool:
        """Check if coupon has unlimited uses."""
        return self.usage_limit is None
    
    @property
    def discount_display(self) -> str:
        """Get discount display string."""
        if self.discount_type == CouponType.PERCENTAGE.value:
            return f"{self.discount_value}% OFF"
        return f"{self.discount_value} PKR OFF"
    
    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.is_active:
            return "🟢 Active"
        elif self.is_expired:
            return "🔴 Expired"
        elif self.is_depleted:
            return "🔴 Depleted"
        elif self.is_inactive:
            return "⚪ Inactive"
        return "Unknown"
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until coupon expiry."""
        if self.end_date is None:
            return -1
        delta = self.end_date - func.now()
        return max(0, delta.days)
    
    @property
    def days_since_start(self) -> int:
        """Get days since coupon start."""
        if self.start_date is None:
            return 0
        delta = func.now() - self.start_date
        return max(0, delta.days)
    
    @property
    def usage_rate(self) -> float:
        """Calculate usage rate."""
        if self.usage_limit is None:
            return 0.0
        if self.usage_limit == 0:
            return 0.0
        return (self.used_count / self.usage_limit) * 100
    
    @property
    def target_display(self) -> str:
        """Get human-readable target display."""
        if self.target_type == CouponTargetType.ALL.value:
            return "📚 All Courses"
        elif self.target_type == CouponTargetType.COURSE.value:
            return f"🎯 Course ID: {self.target_id}"
        elif self.target_type == CouponTargetType.LEARNING_PATH.value:
            return f"🛤️ Path ID: {self.target_id}"
        return "Unknown"
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def activate(self) -> None:
        """Activate the coupon."""
        self.status = CouponStatus.ACTIVE.value
    
    def deactivate(self) -> None:
        """Deactivate the coupon."""
        self.status = CouponStatus.INACTIVE.value
    
    def expire(self) -> None:
        """Mark coupon as expired."""
        self.status = CouponStatus.EXPIRED.value
    
    def mark_depleted(self) -> None:
        """Mark coupon as depleted."""
        self.status = CouponStatus.DEPLETED.value
    
    def increment_usage(self) -> None:
        """Increment usage count."""
        self.used_count += 1
        
        # Check if usage limit reached
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            self.mark_depleted()
    
    def decrement_usage(self) -> None:
        """Decrement usage count (for refunds)."""
        if self.used_count > 0:
            self.used_count -= 1
            # Reactivate if was depleted
            if self.status == CouponStatus.DEPLETED.value:
                self.status = CouponStatus.ACTIVE.value
    
    def check_validity(self, user_id: int = None, amount: float = 0.0) -> dict:
        """
        Check if coupon is valid for use.
        
        Returns:
            dict: {'valid': bool, 'message': str, 'discount_amount': float}
        """
        # Check status
        if not self.is_active:
            return {
                'valid': False,
                'message': 'Coupon is not active',
                'discount_amount': 0.0
            }
        
        # Check date range
        if not self.is_within_date_range:
            return {
                'valid': False,
                'message': 'Coupon has expired or not yet started',
                'discount_amount': 0.0
            }
        
        # Check usage limit
        if self.is_usage_limit_reached:
            return {
                'valid': False,
                'message': 'Coupon usage limit has been reached',
                'discount_amount': 0.0
            }
        
        # Check minimum purchase amount
        if amount < float(self.min_purchase_amount):
            return {
                'valid': False,
                'message': f'Minimum purchase amount of {self.min_purchase_amount} required',
                'discount_amount': 0.0
            }
        
        # Check per-user limit
        if user_id and self.per_user_limit > 0:
            user_usage = sum(1 for u in self.usages if u.user_id == user_id and u.status == CouponUsageStatus.USED.value)
            if user_usage >= self.per_user_limit:
                return {
                    'valid': False,
                    'message': f'You have already used this coupon {self.per_user_limit} time(s)',
                    'discount_amount': 0.0
                }
        
        # Calculate discount amount
        discount_amount = self.calculate_discount(amount)
        
        return {
            'valid': True,
            'message': 'Coupon is valid',
            'discount_amount': discount_amount
        }
    
    def calculate_discount(self, amount: float) -> float:
        """Calculate discount amount for a given purchase amount."""
        if self.discount_type == CouponType.PERCENTAGE.value:
            discount = amount * (float(self.discount_value) / 100)
            if self.max_discount_amount is not None:
                discount = min(discount, float(self.max_discount_amount))
            return discount
        else:  # FIXED
            return min(float(self.discount_value), amount)
    
    def get_discounted_price(self, amount: float) -> float:
        """Get discounted price after applying coupon."""
        discount = self.calculate_discount(amount)
        return max(0, amount - discount)
    
    def soft_delete_coupon(self) -> None:
        """Soft delete the coupon."""
        self.status = CouponStatus.DELETED.value
        self.deleted_at = func.now()
    
    def restore_coupon(self) -> None:
        """Restore a soft-deleted coupon."""
        self.status = CouponStatus.ACTIVE.value
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
    def validate_code(code: str) -> bool:
        """Validate coupon code."""
        import re
        return bool(re.match(r'^[A-Z0-9\-_]{3,50}$', code))
    
    @staticmethod
    def validate_discount_value(value: float, discount_type: str) -> bool:
        """Validate discount value."""
        if discount_type == CouponType.PERCENTAGE.value:
            return 0 <= value <= 100
        else:  # FIXED
            return value >= 0
    
    @staticmethod
    def validate_min_purchase_amount(amount: float) -> bool:
        """Validate minimum purchase amount."""
        return amount >= 0
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert coupon to dictionary."""
        data = {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value),
            "discount_display": self.discount_display,
            "max_discount_amount": float(self.max_discount_amount) if self.max_discount_amount else None,
            "min_purchase_amount": float(self.min_purchase_amount) if self.min_purchase_amount else 0.0,
            "target_type": self.target_type,
            "target_display": self.target_display,
            "target_id": self.target_id,
            "usage_limit": self.usage_limit,
            "used_count": self.used_count,
            "remaining_uses": self.remaining_uses,
            "has_unlimited_uses": self.has_unlimited_uses,
            "per_user_limit": self.per_user_limit,
            "first_time_only": self.first_time_only,
            "status": self.status,
            "display_status": self.display_status,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "is_depleted": self.is_depleted,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "days_until_expiry": self.days_until_expiry,
            "days_since_start": self.days_since_start,
            "usage_rate": self.usage_rate,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "grace_period_days": self.grace_period_days,
                "metadata": self.metadata,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing coupon data (safe for API responses)."""
        data = self.to_dict()
        # Remove sensitive fields for public view
        data.pop("created_by", None)
        data.pop("created_by_name", None)
        data.pop("metadata", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing coupon data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 2. COUPON USAGE MODEL
# ============================================================

class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    # ============================================================
    # PRIMARY KEY
    # ============================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # NEW: Learning path enrollment
    path_enrollment_id = Column(Integer, ForeignKey("path_enrollments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ============================================================
    # USAGE DETAILS
    # ============================================================
    discount_applied = Column(DECIMAL(10, 2), nullable=False)
    original_amount = Column(DECIMAL(10, 2), nullable=False)
    final_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # ============================================================
    # STATUS
    # ============================================================
    status = Column(
        String(20),
        default=CouponUsageStatus.USED.value,
        nullable=False,
        index=True
    )
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================================
    # NEW: IP & DEVICE
    # ============================================================
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # ============================================================
    # CONSTRAINTS
    # ============================================================
    __table_args__ = (
        Index('ix_coupon_usages_unique', 'coupon_id', 'user_id', 'enrollment_id', unique=True),
        Index('ix_coupon_usages_coupon', 'coupon_id'),
        Index('ix_coupon_usages_user', 'user_id'),
        Index('ix_coupon_usages_enrollment', 'enrollment_id'),
        Index('ix_coupon_usages_status', 'status'),
        Index('ix_coupon_usages_used_at', 'used_at'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    coupon = relationship(
        "Coupon",
        back_populates="usages",
        foreign_keys=[coupon_id]
    )
    
    user = relationship(
        "User",
        back_populates="coupon_usages",
        foreign_keys=[user_id]
    )
    
    enrollment = relationship(
        "Enrollment",
        back_populates="coupon_usage",
        foreign_keys=[enrollment_id],
        uselist=False
    )
    
    # NEW: Path enrollment relationship
    path_enrollment = relationship(
        "PathEnrollment",
        foreign_keys=[path_enrollment_id],
        uselist=False
    )
    
    # ============================================================
    # REPRESENTATION
    # ============================================================
    
    def __repr__(self) -> str:
        return f"<CouponUsage {self.id}: {self.user_id} -> {self.coupon_id}>"
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_used(self) -> bool:
        """Check if usage is active."""
        return self.status == CouponUsageStatus.USED.value
    
    @property
    def is_cancelled_usage(self) -> bool:
        """Check if usage was cancelled."""
        return self.status == CouponUsageStatus.CANCELLED.value
    
    @property
    def is_expired_usage(self) -> bool:
        """Check if usage is expired."""
        return self.status == CouponUsageStatus.EXPIRED.value
    
    @property
    def savings_display(self) -> str:
        """Get savings display."""
        return f"Saved {self.discount_applied} PKR"
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def cancel(self) -> None:
        """Cancel this coupon usage."""
        self.status = CouponUsageStatus.CANCELLED.value
        self.cancelled_at = func.now()
        # Decrement coupon usage count
        if self.coupon:
            self.coupon.decrement_usage()
    
    def expire_usage(self) -> None:
        """Mark usage as expired."""
        self.status = CouponUsageStatus.EXPIRED.value
    
    # ============================================================
    # SERIALIZATION
    # ============================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert coupon usage to dictionary."""
        data = {
            "id": self.id,
            "coupon_id": self.coupon_id,
            "coupon_code": self.coupon.code if self.coupon else None,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "enrollment_id": self.enrollment_id,
            "path_enrollment_id": self.path_enrollment_id,
            "discount_applied": float(self.discount_applied),
            "original_amount": float(self.original_amount),
            "final_amount": float(self.final_amount),
            "savings_display": self.savings_display,
            "status": self.status,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
        
        if include_sensitive:
            data.update({
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
            })
        
        return data
    
    def to_public_json(self) -> dict:
        """Public-facing coupon usage data."""
        data = self.to_dict()
        data.pop("user_name", None)
        data.pop("ip_address", None)
        data.pop("user_agent", None)
        return data
    
    def to_admin_json(self) -> dict:
        """Admin-facing coupon usage data (full access)."""
        return self.to_dict(include_sensitive=True)


# ============================================================
# 3. COUPON AUDIT LOG
# ============================================================

class CouponAuditLog(Base):
    """Track coupon creation, modification, and usage events."""
    __tablename__ = "coupon_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # created, updated, activated, deactivated, deleted, used
    event_data = Column(JSON, nullable=True)
    
    # Who performed the action
    performed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Timestamp
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Context
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    coupon = relationship("Coupon", foreign_keys=[coupon_id])
    performer = relationship("User", foreign_keys=[performed_by])
    
    __table_args__ = (
        Index('ix_coupon_audit_coupon', 'coupon_id'),
        Index('ix_coupon_audit_performed_by', 'performed_by'),
        Index('ix_coupon_audit_performed_at', 'performed_at'),
        Index('ix_coupon_audit_event', 'event_type'),
    )
    
    def __repr__(self) -> str:
        return f"<CouponAuditLog {self.id}: {self.event_type}>"