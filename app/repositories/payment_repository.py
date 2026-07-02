# ============================================================
# AETHER LINK - PAYMENT REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, extract
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.payments import Payment, PaymentStatus, PaymentMethod
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.user import User
from ..models.course import Course


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment model operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Payment)
    
    # ============================================================
    # FIND OPERATIONS
    # ============================================================
    
    def get_by_student(self, student_id: int) -> List[Payment]:
        """Get all payments for a student."""
        return self.db.query(Payment).filter(
            Payment.student_id == student_id,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.created_at.desc()).all()
    
    def get_by_student_paginated(
        self, 
        student_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Payment], int]:
        """Get paginated payments for a student."""
        query = self.db.query(Payment).filter(
            Payment.student_id == student_id,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.created_at.desc())
        total = query.count()
        payments = query.offset(skip).limit(limit).all()
        return payments, total
    
    def get_by_enrollment(self, enrollment_id: int) -> Optional[Payment]:
        """Get payment by enrollment ID."""
        return self.db.query(Payment).filter(
            Payment.enrollment_id == enrollment_id,
            Payment.deleted_at.is_(None)
        ).first()
    
    def get_by_transaction(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        return self.db.query(Payment).filter(
            Payment.transaction_id == transaction_id,
            Payment.deleted_at.is_(None)
        ).first()
    
    def get_by_status(self, status: PaymentStatus) -> List[Payment]:
        """Get payments by status."""
        return self.db.query(Payment).filter(
            Payment.status == status,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.created_at.desc()).all()
    
    # ============================================================
    # VERIFICATION QUERIES
    # ============================================================
    
    def get_pending_verification(self) -> List[Payment]:
        """Get payments awaiting verification."""
        return self.db.query(Payment).options(
            joinedload(Payment.student),
            joinedload(Payment.enrollment).joinedload(Enrollment.course)
        ).filter(
            Payment.status == PaymentStatus.AWAITING_VERIFICATION,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.created_at).all()
    
    def get_pending_verification_count(self) -> int:
        """Count pending verifications."""
        return self.db.query(Payment).filter(
            Payment.status == PaymentStatus.AWAITING_VERIFICATION,
            Payment.deleted_at.is_(None)
        ).count()
    
    def get_verified(self) -> List[Payment]:
        """Get verified payments."""
        return self.db.query(Payment).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.verified_at.desc()).all()
    
    def get_rejected(self) -> List[Payment]:
        """Get rejected payments."""
        return self.db.query(Payment).filter(
            Payment.status == PaymentStatus.REJECTED,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.rejected_at.desc()).all()
    
    def get_refunded(self) -> List[Payment]:
        """Get refunded payments."""
        return self.db.query(Payment).filter(
            Payment.status == PaymentStatus.REFUNDED,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.refunded_at.desc()).all()
    
    # ============================================================
    # RELATIONSHIP QUERIES
    # ============================================================
    
    def get_with_enrollment(self, payment_id: int) -> Optional[Payment]:
        """Get payment with enrollment loaded."""
        return self.db.query(Payment).options(
            joinedload(Payment.enrollment)
        ).filter(
            Payment.id == payment_id,
            Payment.deleted_at.is_(None)
        ).first()
    
    def get_with_all_relations(self, payment_id: int) -> Optional[Payment]:
        """Get payment with all relationships loaded."""
        return self.db.query(Payment).options(
            joinedload(Payment.student),
            joinedload(Payment.enrollment).joinedload(Enrollment.course),
            joinedload(Payment.verified_by_user),
            joinedload(Payment.refund_processed_by_user)
        ).filter(
            Payment.id == payment_id,
            Payment.deleted_at.is_(None)
        ).first()
    
    # ============================================================
    # PAYMENT OPERATIONS
    # ============================================================
    
    def upload_screenshot(
        self, 
        payment_id: int, 
        screenshot_url: str,
        transaction_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_phone: Optional[str] = None
    ) -> Payment:
        """Upload payment screenshot and update status."""
        payment = self.get_by_id_or_fail(payment_id)
        
        payment.screenshot_url = screenshot_url
        payment.screenshot_uploaded_at = datetime.utcnow()
        payment.status = PaymentStatus.AWAITING_VERIFICATION
        
        if transaction_id:
            payment.transaction_id = transaction_id
        if sender_name:
            payment.sender_name = sender_name
        if sender_phone:
            payment.sender_phone = sender_phone
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def verify_payment(
        self, 
        payment_id: int, 
        verified_by: int,
        notes: Optional[str] = None
    ) -> Payment:
        """Verify a payment and activate enrollment."""
        payment = self.get_by_id_or_fail(payment_id)
        
        payment.status = PaymentStatus.VERIFIED
        payment.verified_by = verified_by
        payment.verified_at = datetime.utcnow()
        
        if notes:
            payment.verification_notes = notes
        
        # Activate enrollment
        enrollment = payment.enrollment
        if enrollment:
            enrollment.status = EnrollmentStatus.ACTIVE
            enrollment.payment_verified = True
            enrollment.payment_verified_by = verified_by
            enrollment.payment_verified_at = datetime.utcnow()
            enrollment.expires_at = datetime.utcnow() + timedelta(days=90)
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def reject_payment(
        self, 
        payment_id: int, 
        verified_by: int,
        reason: str
    ) -> Payment:
        """Reject a payment and cancel enrollment."""
        payment = self.get_by_id_or_fail(payment_id)
        
        payment.status = PaymentStatus.REJECTED
        payment.verified_by = verified_by
        payment.rejected_at = datetime.utcnow()
        payment.rejection_reason = reason
        
        # Cancel enrollment
        enrollment = payment.enrollment
        if enrollment:
            enrollment.status = EnrollmentStatus.CANCELLED
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def refund_payment(
        self, 
        payment_id: int, 
        processed_by: int,
        reason: Optional[str] = None
    ) -> Payment:
        """Refund a payment."""
        payment = self.get_by_id_or_fail(payment_id)
        
        payment.status = PaymentStatus.REFUNDED
        payment.refund_processed_by = processed_by
        payment.refunded_at = datetime.utcnow()
        
        if reason:
            payment.refund_reason = reason
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    # ============================================================
    # STUDENT PAYMENT HISTORY
    # ============================================================
    
    def get_student_payment_history(self, student_id: int) -> List[Dict[str, Any]]:
        """Get student's payment history with course details."""
        payments = self.get_by_student(student_id)
        
        history = []
        for payment in payments:
            course = payment.enrollment.course if payment.enrollment else None
            
            history.append({
                "id": payment.id,
                "amount": float(payment.amount),
                "method": payment.method.value,
                "status": payment.status.value,
                "transaction_id": payment.transaction_id,
                "screenshot_url": payment.screenshot_url,
                "created_at": payment.created_at,
                "verified_at": payment.verified_at,
                "course": {
                    "id": course.id if course else None,
                    "title": course.title if course else None,
                    "slug": course.slug if course else None,
                } if course else None,
                "enrollment_id": payment.enrollment_id,
            })
        
        return history
    
    # ============================================================
    # REVENUE & STATISTICS
    # ============================================================
    
    def get_revenue_stats(self) -> Dict[str, Any]:
        """Get revenue statistics."""
        total_revenue = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).scalar() or 0
        
        total_count = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).count()
        
        # Revenue this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.verified_at >= start_of_month,
            Payment.deleted_at.is_(None)
        ).scalar() or 0
        
        # Average payment
        avg_payment = total_revenue / total_count if total_count > 0 else 0
        
        return {
            "total_revenue": float(total_revenue),
            "total_transactions": total_count,
            "monthly_revenue": float(monthly_revenue),
            "average_payment": float(avg_payment),
            "pending_verification": self.get_pending_verification_count(),
        }
    
    def get_revenue_by_course(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by course."""
        results = self.db.query(
            Course.id.label('course_id'),
            Course.title.label('course_title'),
            func.count(Payment.id).label('transaction_count'),
            func.sum(Payment.amount).label('total_revenue')
        ).join(Enrollment).join(Course).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).group_by(Course.id).order_by(func.sum(Payment.amount).desc()).all()
        
        return [
            {
                "course_id": r.course_id,
                "course_title": r.course_title,
                "transaction_count": r.transaction_count,
                "total_revenue": float(r.total_revenue),
            }
            for r in results
        ]
    
    def get_revenue_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get revenue by date range (daily breakdown)."""
        results = self.db.query(
            func.date(Payment.verified_at).label('date'),
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.verified_at >= start_date,
            Payment.verified_at <= end_date,
            Payment.deleted_at.is_(None)
        ).group_by(func.date(Payment.verified_at)).order_by('date').all()
        
        return [
            {
                "date": r.date,
                "count": r.count,
                "total": float(r.total),
            }
            for r in results
        ]
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get admin dashboard payment statistics."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today's revenue
        today_revenue = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.verified_at >= today_start,
            Payment.deleted_at.is_(None)
        ).scalar() or 0
        
        # This month's revenue
        start_of_month = today_start.replace(day=1)
        month_revenue = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.verified_at >= start_of_month,
            Payment.deleted_at.is_(None)
        ).scalar() or 0
        
        # Pending count
        pending = self.get_pending_verification_count()
        
        # Total revenue
        total = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).scalar() or 0
        
        # Transaction count
        total_transactions = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).count()
        
        return {
            "today_revenue": float(today_revenue),
            "month_revenue": float(month_revenue),
            "total_revenue": float(total),
            "total_transactions": total_transactions,
            "pending_verification": pending,
            "recent_transactions": self._get_recent_transactions(5),
        }
    
    def _get_recent_transactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent verified transactions."""
        payments = self.db.query(Payment).options(
            joinedload(Payment.student),
            joinedload(Payment.enrollment).joinedload(Enrollment.course)
        ).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).order_by(Payment.verified_at.desc()).limit(limit).all()
        
        return [
            {
                "id": p.id,
                "amount": float(p.amount),
                "student_name": p.student.full_name if p.student else None,
                "student_email": p.student.email if p.student else None,
                "course_title": p.enrollment.course.title if p.enrollment and p.enrollment.course else None,
                "verified_at": p.verified_at,
                "method": p.method.value,
            }
            for p in payments
        ]
    
    # ============================================================
    # VALIDATION OPERATIONS
    # ============================================================
    
    def is_payment_completed(self, enrollment_id: int) -> bool:
        """Check if a payment is completed for an enrollment."""
        payment = self.get_by_enrollment(enrollment_id)
        if not payment:
            return False
        return payment.status == PaymentStatus.VERIFIED
    
    def has_pending_payment(self, student_id: int, course_id: int) -> bool:
        """Check if student has a pending payment for a course."""
        payment = self.db.query(Payment).join(Enrollment).filter(
            Payment.student_id == student_id,
            Enrollment.course_id == course_id,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.AWAITING_VERIFICATION]),
            Payment.deleted_at.is_(None)
        ).first()
        return payment is not None
    
    # ============================================================
    # METHOD STATISTICS
    # ============================================================
    
    def get_payment_method_stats(self) -> Dict[str, Any]:
        """Get payment method statistics."""
        results = self.db.query(
            Payment.method,
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.status == PaymentStatus.VERIFIED,
            Payment.deleted_at.is_(None)
        ).group_by(Payment.method).all()
        
        return {
            r.method.value: {
                "count": r.count,
                "total": float(r.total),
            }
            for r in results
        }