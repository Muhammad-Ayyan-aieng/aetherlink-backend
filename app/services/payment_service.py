# ============================================================
# AETHER LINK - PAYMENT SERVICE
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..repositories.payment_repository import PaymentRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..repositories.user_repository import UserRepository
from ..repositories.course_repository import CourseRepository
from ..models.payments import PaymentStatus
from ..models.enrollment import EnrollmentStatus
from ..models.user import UserRole
from ..schemas.payment import PaymentInitiate, PaymentUploadScreenshot


class PaymentService:
    """Service for payment business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.user_repo = UserRepository(db)
        self.course_repo = CourseRepository(db)
    
    # ============================================================
    # INITIATE PAYMENT
    # ============================================================
    
    def initiate_payment(self, enrollment_id: int, student_id: int) -> Dict[str, Any]:
        """
        Initiate payment for an enrollment.
        
        Args:
            enrollment_id: Enrollment ID
            student_id: Student ID
            
        Returns:
            Payment details
            
        Raises:
            ValueError: If validation fails
        """
        # Check enrollment exists and belongs to student
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if enrollment.student_id != student_id:
            raise ValueError("You don't have permission to pay for this enrollment")
        
        if enrollment.status == EnrollmentStatus.ACTIVE:
            raise ValueError("Enrollment is already active")
        
        if enrollment.status == EnrollmentStatus.COMPLETED:
            raise ValueError("Enrollment is already completed")
        
        # Check if payment already exists
        existing_payment = self.payment_repo.get_by_enrollment(enrollment_id)
        if existing_payment:
            if existing_payment.status == PaymentStatus.VERIFIED:
                raise ValueError("Payment already verified")
            elif existing_payment.status == PaymentStatus.AWAITING_VERIFICATION:
                return self._format_payment_response(existing_payment)
            elif existing_payment.status == PaymentStatus.PENDING:
                return self._format_payment_response(existing_payment)
            elif existing_payment.status == PaymentStatus.REJECTED:
                # Allow new payment if rejected
                existing_payment.status = PaymentStatus.PENDING
                self.db.commit()
                self.db.refresh(existing_payment)
                return self._format_payment_response(existing_payment)
        
        # Create payment
        payment = self.payment_repo.create(
            enrollment_id=enrollment_id,
            student_id=student_id,
            amount=enrollment.payment_amount,
            method="easypaisa",
            status=PaymentStatus.PENDING.value,
            easypaisa_account="03XX-XXXXXXX",
            easypaisa_holder="Aether Link Pvt Ltd",
        )
        
        # Update enrollment status
        enrollment.status = EnrollmentStatus.PENDING
        self.db.commit()
        self.db.refresh(enrollment)
        self.db.refresh(payment)
        
        return self._format_payment_response(payment)
    
    # ============================================================
    # UPLOAD SCREENSHOT
    # ============================================================
    
    def upload_screenshot(
        self, 
        payment_id: int,
        screenshot_data: PaymentUploadScreenshot,
        student_id: int
    ) -> Dict[str, Any]:
        """
        Upload payment screenshot.
        
        Args:
            payment_id: Payment ID
            screenshot_data: Screenshot data
            student_id: Student ID
            
        Returns:
            Updated payment
            
        Raises:
            ValueError: If validation fails
        """
        # Check payment exists and belongs to student
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.student_id != student_id:
            raise ValueError("You don't have permission to update this payment")
        
        if payment.status == PaymentStatus.VERIFIED:
            raise ValueError("Payment already verified")
        
        if payment.status == PaymentStatus.REJECTED:
            raise ValueError("Payment was rejected. Please contact support.")
        
        # Upload screenshot
        payment = self.payment_repo.upload_screenshot(
            payment_id=payment_id,
            screenshot_url=screenshot_data.screenshot_url,
            transaction_id=screenshot_data.transaction_id,
            sender_name=screenshot_data.sender_name,
            sender_phone=screenshot_data.sender_phone,
        )
        
        # Update enrollment status
        enrollment = self.enrollment_repo.get_by_id(payment.enrollment_id)
        if enrollment:
            enrollment.status = EnrollmentStatus.PAYMENT_VERIFICATION
            enrollment.payment_screenshot = screenshot_data.screenshot_url
            self.db.commit()
            self.db.refresh(enrollment)
        
        return self._format_payment_response(payment)
    
    # ============================================================
    # VERIFY PAYMENT (Admin)
    # ============================================================
    
    def verify_payment(
        self, 
        payment_id: int, 
        admin_id: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a payment (admin only).
        
        Args:
            payment_id: Payment ID
            admin_id: Admin ID
            notes: Verification notes
            
        Returns:
            Verified payment
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        # Check payment exists
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status == PaymentStatus.VERIFIED:
            raise ValueError("Payment already verified")
        
        if payment.status != PaymentStatus.AWAITING_VERIFICATION:
            raise ValueError("Payment is not awaiting verification")
        
        # Verify payment
        payment = self.payment_repo.verify_payment(
            payment_id=payment_id,
            verified_by=admin_id,
            notes=notes,
        )
        
        return self._format_payment_response(payment)
    
    # ============================================================
    # REJECT PAYMENT (Admin)
    # ============================================================
    
    def reject_payment(
        self, 
        payment_id: int, 
        admin_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Reject a payment (admin only).
        
        Args:
            payment_id: Payment ID
            admin_id: Admin ID
            reason: Rejection reason
            
        Returns:
            Rejected payment
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        # Check payment exists
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status == PaymentStatus.VERIFIED:
            raise ValueError("Payment already verified")
        
        if payment.status == PaymentStatus.REJECTED:
            raise ValueError("Payment already rejected")
        
        # Reject payment
        payment = self.payment_repo.reject_payment(
            payment_id=payment_id,
            verified_by=admin_id,
            reason=reason,
        )
        
        return self._format_payment_response(payment)
    
    # ============================================================
    # REFUND PAYMENT (Admin)
    # ============================================================
    
    def refund_payment(
        self, 
        payment_id: int, 
        admin_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment (admin only).
        
        Args:
            payment_id: Payment ID
            admin_id: Admin ID
            reason: Refund reason
            
        Returns:
            Refunded payment
            
        Raises:
            ValueError: If validation fails or permission denied
        """
        # Check admin exists
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        # Check payment exists
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status != PaymentStatus.VERIFIED:
            raise ValueError("Only verified payments can be refunded")
        
        # Refund payment
        payment = self.payment_repo.refund_payment(
            payment_id=payment_id,
            processed_by=admin_id,
            reason=reason,
        )
        
        # Cancel enrollment
        enrollment = self.enrollment_repo.get_by_id(payment.enrollment_id)
        if enrollment:
            enrollment.status = EnrollmentStatus.CANCELLED
            self.db.commit()
            self.db.refresh(enrollment)
        
        return self._format_payment_response(payment)
    
    # ============================================================
    # GET PAYMENT HISTORY (Student)
    # ============================================================
    
    def get_payment_history(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get payment history for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            Payment history
        """
        return self.payment_repo.get_student_payment_history(student_id)
    
    def get_payment_by_enrollment(self, enrollment_id: int, student_id: int) -> Dict[str, Any]:
        """
        Get payment for an enrollment.
        
        Args:
            enrollment_id: Enrollment ID
            student_id: Student ID
            
        Returns:
            Payment details
            
        Raises:
            ValueError: If validation fails
        """
        enrollment = self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        if enrollment.student_id != student_id:
            raise ValueError("You don't have permission to view this payment")
        
        payment = self.payment_repo.get_by_enrollment(enrollment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        return self._format_payment_response(payment)
    
    # ============================================================
    # GET PENDING PAYMENTS (Admin)
    # ============================================================
    
    def get_pending_payments(self, admin_id: int) -> List[Dict[str, Any]]:
        """
        Get pending payment verifications (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Pending payments
            
        Raises:
            ValueError: If permission denied
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        payments = self.payment_repo.get_pending_verification()
        
        return [
            {
                "id": p.id,
                "amount": float(p.amount),
                "method": p.method.value,
                "student_name": p.student.full_name if p.student else None,
                "student_email": p.student.email if p.student else None,
                "course_title": p.enrollment.course.title if p.enrollment and p.enrollment.course else None,
                "screenshot_url": p.screenshot_url,
                "sender_name": p.sender_name,
                "sender_phone": p.sender_phone,
                "transaction_id": p.transaction_id,
                "created_at": p.created_at,
                "screenshot_uploaded_at": p.screenshot_uploaded_at,
            }
            for p in payments
        ]
    
    def get_pending_count(self, admin_id: int) -> int:
        """
        Get count of pending verifications.
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Pending count
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.payment_repo.get_pending_verification_count()
    
    # ============================================================
    # REVENUE & STATISTICS (Admin)
    # ============================================================
    
    def get_revenue_stats(self, admin_id: int) -> Dict[str, Any]:
        """
        Get revenue statistics (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Revenue statistics
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.payment_repo.get_revenue_stats()
    
    def get_dashboard_stats(self, admin_id: int) -> Dict[str, Any]:
        """
        Get payment dashboard statistics (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Dashboard statistics
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.payment_repo.get_dashboard_stats()
    
    def get_revenue_by_course(self, admin_id: int) -> List[Dict[str, Any]]:
        """
        Get revenue breakdown by course (admin only).
        
        Args:
            admin_id: Admin ID
            
        Returns:
            Revenue by course
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != UserRole.ADMIN:
            raise ValueError("Admin access required")
        
        return self.payment_repo.get_revenue_by_course()
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _format_payment_response(self, payment: Any) -> Dict[str, Any]:
        """Format payment for response."""
        return {
            "id": payment.id,
            "enrollment_id": payment.enrollment_id,
            "student_id": payment.student_id,
            "amount": float(payment.amount),
            "method": payment.method.value,
            "status": payment.status.value,
            "easypaisa_account": payment.easypaisa_account,
            "easypaisa_holder": payment.easypaisa_holder,
            "sender_name": payment.sender_name,
            "sender_phone": payment.sender_phone,
            "transaction_id": payment.transaction_id,
            "screenshot_url": payment.screenshot_url,
            "screenshot_uploaded_at": payment.screenshot_uploaded_at,
            "verified_by": payment.verified_by,
            "verified_at": payment.verified_at,
            "verification_notes": payment.verification_notes,
            "rejected_at": payment.rejected_at,
            "rejection_reason": payment.rejection_reason,
            "refunded_at": payment.refunded_at,
            "refund_reason": payment.refund_reason,
            "created_at": payment.created_at,
        }