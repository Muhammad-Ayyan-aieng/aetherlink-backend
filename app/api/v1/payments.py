# ============================================================
# AETHER LINK - PAYMENTS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any

from ...core.database import get_db
from ...core.dependencies import (
    get_current_user,
    get_current_admin_user,
    rate_limiter,
)
from ...services.payment_service import PaymentService
from ...services.enrollment_service import EnrollmentService
from ...schemas.payment import (
    PaymentInitiate,
    PaymentUploadScreenshot,
    PaymentVerify,
    PaymentReject,
    PaymentRefund,
    PaymentResponse,
    PaymentHistoryResponse,
    PaymentListResponse,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/payments", tags=["Payments"])


# ============================================================
# STUDENT: INITIATE PAYMENT
# ============================================================

@router.post(
    "/initiate",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter)],
    summary="Initiate payment",
    description="Initiate payment for an enrollment.",
)
def initiate_payment(
    payment_data: PaymentInitiate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Initiate payment for an enrollment.
    
    **Student only.**
    
    - **enrollment_id**: Enrollment ID
    - **method**: Payment method (easypaisa, jazzcash, etc.)
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can initiate payments",
            )
        
        payment_service = PaymentService(db)
        result = payment_service.initiate_payment(
            enrollment_id=payment_data.enrollment_id,
            student_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: UPLOAD SCREENSHOT
# ============================================================

@router.post(
    "/upload-screenshot",
    response_model=PaymentResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Upload payment screenshot",
    description="Upload payment screenshot for verification.",
)
def upload_screenshot(
    upload_data: PaymentUploadScreenshot,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload payment screenshot.
    
    **Student only.**
    
    - **payment_id**: Payment ID
    - **screenshot_url**: URL to the screenshot
    - **transaction_id**: Optional transaction ID
    - **sender_name**: Optional sender name
    - **sender_phone**: Optional sender phone
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can upload screenshots",
            )
        
        payment_service = PaymentService(db)
        result = payment_service.upload_screenshot(
            payment_id=upload_data.payment_id,
            screenshot_data=upload_data,
            student_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: PAYMENT HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=List[PaymentHistoryResponse],
    dependencies=[Depends(rate_limiter)],
    summary="Get payment history",
    description="Get payment history for the current student.",
)
def get_payment_history(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get payment history for the current student.
    
    - **status**: Filter by payment status
    - **skip**: Pagination offset
    - **limit**: Max results (1-100)
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their payment history",
            )
        
        payment_service = PaymentService(db)
        history = payment_service.get_payment_history(current_user.id)
        
        # Apply filters
        if status:
            history = [h for h in history if h["status"] == status]
        
        # Apply pagination
        total = len(history)
        history = history[skip:skip + limit]
        
        return history
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: PENDING PAYMENTS
# ============================================================

@router.get(
    "/pending",
    response_model=List[dict],
    dependencies=[Depends(get_current_admin_user)],
    summary="Get pending verifications",
    description="Get all pending payment verifications (admin only).",
)
def get_pending_payments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get pending payment verifications.
    
    **Admin only.**
    """
    try:
        payment_service = PaymentService(db)
        pending = payment_service.get_pending_payments(current_user.id)
        return pending
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: VERIFY PAYMENT
# ============================================================

@router.post(
    "/verify",
    response_model=PaymentResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Verify payment",
    description="Verify a payment (admin only).",
)
def verify_payment(
    verify_data: PaymentVerify,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Verify a payment.
    
    **Admin only.**
    
    - **payment_id**: Payment ID
    - **notes**: Optional verification notes
    """
    try:
        payment_service = PaymentService(db)
        result = payment_service.verify_payment(
            payment_id=verify_data.payment_id,
            admin_id=current_user.id,
            notes=verify_data.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: REJECT PAYMENT
# ============================================================

@router.post(
    "/reject",
    response_model=PaymentResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Reject payment",
    description="Reject a payment (admin only).",
)
def reject_payment(
    reject_data: PaymentReject,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Reject a payment.
    
    **Admin only.**
    
    - **payment_id**: Payment ID
    - **reason**: Rejection reason
    """
    try:
        payment_service = PaymentService(db)
        result = payment_service.reject_payment(
            payment_id=reject_data.payment_id,
            admin_id=current_user.id,
            reason=reject_data.reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: REFUND PAYMENT
# ============================================================

@router.post(
    "/refund",
    response_model=PaymentResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Refund payment",
    description="Refund a payment (admin only).",
)
def refund_payment(
    refund_data: PaymentRefund,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Refund a payment.
    
    **Admin only.**
    
    - **payment_id**: Payment ID
    - **reason**: Optional refund reason
    """
    try:
        payment_id = refund_data.payment_id
        reason = refund_data.reason
        
        payment_service = PaymentService(db)
        result = payment_service.refund_payment(
            payment_id=payment_id,
            admin_id=current_user.id,
            reason=reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: PAYMENT STATISTICS
# ============================================================

@router.get(
    "/stats",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get payment statistics",
    description="Get payment statistics (admin only).",
)
def get_payment_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get payment statistics.
    
    **Admin only.**
    """
    try:
        payment_service = PaymentService(db)
        stats = payment_service.get_dashboard_stats(current_user.id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: REVENUE BY COURSE
# ============================================================

@router.get(
    "/revenue/courses",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get revenue by course",
    description="Get revenue breakdown by course (admin only).",
)
def get_revenue_by_course(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get revenue breakdown by course.
    
    **Admin only.**
    """
    try:
        payment_service = PaymentService(db)
        revenue = payment_service.get_revenue_by_course(current_user.id)
        return revenue
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )