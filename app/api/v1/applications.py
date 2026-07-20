# ============================================================
# AETHER LINK - APPLICATIONS API
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
from ...services.application_service import ApplicationService
from ...schemas.application import (
    ApplicationSubmit,
    ApplicationUpdateStatus,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationStats,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/applications", tags=["Applications"])


# ============================================================
# PUBLIC: SUBMIT APPLICATION (WITH USER CREATION)
# ============================================================

@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter)],
    summary="Submit application",
    description="Submit a course application. Creates user account and sets status to pending.",
)
def submit_application(
    data: ApplicationSubmit,
    db: Session = Depends(get_db),
) -> Any:
    """
    Submit a new course application.
    
    **Public access - no authentication required.**
    
    This will:
    1. Create a new user account (is_active=False)
    2. Create an application (status='pending')
    3. Send email notification to admin
    
    - **email**: Student email
    - **full_name**: Student full name
    - **phone**: Optional phone number
    - **course_id**: Course ID
    - **message**: Optional message
    - **payment_screenshot**: Payment screenshot URL (optional)
    """
    try:
        application_service = ApplicationService(db)
        result = application_service.submit_application(data)
        
        # Return a more detailed response
        return {
            "message": "Application submitted successfully! You will receive an email once approved.",
            "application_id": result.get("application_id"),
            "user_id": result.get("user_id"),
            "status": "pending",
            "requires_approval": True,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# STUDENT: GET MY APPLICATIONS
# ============================================================

@router.get(
    "/me",
    response_model=List[ApplicationResponse],
    dependencies=[Depends(rate_limiter)],
    summary="Get my applications",
    description="Get all applications for the current student.",
)
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all applications for the current student.
    
    **Requires authentication.**
    """
    try:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their applications",
            )
        
        application_service = ApplicationService(db)
        result = application_service.get_student_applications(current_user.email)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: GET ALL APPLICATIONS
# ============================================================

@router.get(
    "/admin",
    response_model=ApplicationListResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get all applications",
    description="Get all applications (admin only).",
)
def get_all_applications(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all applications.
    
    **Admin only.**
    """
    try:
        application_service = ApplicationService(db)
        result = application_service.get_all_applications(
            admin_id=current_user.id,
            status=status,
            search=search,
            skip=skip,
            limit=limit,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: GET APPLICATION DETAILS
# ============================================================

@router.get(
    "/admin/{application_id}",
    response_model=ApplicationResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get application details",
    description="Get application details (admin only).",
)
def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get application details.
    
    **Admin only.**
    """
    try:
        application_service = ApplicationService(db)
        result = application_service.get_application(
            application_id=application_id,
            admin_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# ADMIN: APPROVE APPLICATION
# ============================================================

@router.put(
    "/admin/{application_id}/approve",
    response_model=dict,
    dependencies=[Depends(get_current_admin_user)],
    summary="Approve application",
    description="Approve an application. Activates user account and enrolls them in the course.",
)
def approve_application(
    application_id: int,
    data: ApplicationUpdateStatus = ApplicationUpdateStatus(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Approve an application.
    
    **Admin only.**
    
    This will:
    1. Activate the user account (is_active=True)
    2. Create an enrollment for the user in the course
    3. Send email notification to the user
    
    - **notes**: Optional admin notes
    """
    try:
        application_service = ApplicationService(db)
        result = application_service.approve_application(
            application_id=application_id,
            admin_id=current_user.id,
            notes=data.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: REJECT APPLICATION
# ============================================================

@router.put(
    "/admin/{application_id}/reject",
    response_model=dict,
    dependencies=[Depends(get_current_admin_user)],
    summary="Reject application",
    description="Reject an application (admin only).",
)
def reject_application(
    application_id: int,
    data: ApplicationUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Reject an application.
    
    **Admin only.**
    
    - **notes**: Rejection reason (required)
    """
    try:
        if not data.notes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required",
            )
        
        application_service = ApplicationService(db)
        result = application_service.reject_application(
            application_id=application_id,
            admin_id=current_user.id,
            notes=data.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: APPLICATION STATISTICS
# ============================================================

@router.get(
    "/admin/stats",
    response_model=ApplicationStats,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get application statistics",
    description="Get application statistics (admin only).",
)
def get_application_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get application statistics.
    
    **Admin only.**
    """
    try:
        application_service = ApplicationService(db)
        result = application_service.get_application_stats(current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )