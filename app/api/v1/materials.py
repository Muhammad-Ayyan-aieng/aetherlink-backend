# ============================================================
# AETHER LINK - MATERIALS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any

from ...core.database import get_db
from ...core.dependencies import (
    get_current_user,
    get_current_teacher_user,
    get_current_admin_user,
    rate_limiter,
)
from ...services.material_service import MaterialService
from ...services.course_service import CourseService
from ...services.enrollment_service import EnrollmentService
from ...schemas.material import (
    MaterialUpload,
    MaterialUpdate,
    MaterialResponse,
    MaterialListResponse,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/materials", tags=["Materials"])


# ============================================================
# PUBLIC/ENROLLED: COURSE MATERIALS
# ============================================================

@router.get(
    "/course/{course_id}",
    response_model=MaterialListResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get course materials",
    description="Get all materials for a course.",
)
def get_course_materials(
    course_id: int,
    published_only: bool = Query(True, description="Only published materials"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get materials for a course.
    
    - **course_id**: Course ID
    - **published_only**: Only show published materials
    - **skip**: Pagination offset
    - **limit**: Max results (1-100)
    """
    try:
        material_service = MaterialService(db)
        
        # Check if user has access to unpublished materials
        user_id = current_user.id if current_user else None
        if not user_id:
            # Guest - only published materials
            published_only = True
        
        result = material_service.get_course_materials(
            course_id=course_id,
            user_id=user_id if user_id else 0,
            published_only=published_only,
            skip=skip,
            limit=limit,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get material by ID",
    description="Get a course material by ID.",
)
def get_material(
    material_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a material by ID.
    
    - **material_id**: Material ID
    """
    try:
        material_service = MaterialService(db)
        
        user_id = current_user.id if current_user else 0
        result = material_service.get_material(
            material_id=material_id,
            user_id=user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/search",
    dependencies=[Depends(rate_limiter)],
    summary="Search materials",
    description="Search course materials.",
)
def search_materials(
    q: str = Query(..., min_length=2, description="Search query"),
    course_id: Optional[int] = Query(None, description="Filter by course"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Search materials by title or description.
    
    - **q**: Search query (minimum 2 characters)
    - **course_id**: Optional course filter
    - **file_type**: Optional file type filter
    """
    try:
        material_service = MaterialService(db)
        
        user_id = current_user.id if current_user else 0
        results = material_service.search_materials(
            query=q,
            user_id=user_id,
            course_id=course_id,
            file_type=file_type,
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: MATERIAL CRUD
# ============================================================

@router.post(
    "/",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Upload material",
    description="Upload a course material (teacher or admin).",
)
def upload_material(
    material_data: MaterialUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload a course material.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - **title**: Material title
    - **file_type**: pdf, pptx, doc, docx, link
    - **file_url**: URL to the file (for files)
    - **link_url**: URL to the link (for links)
    """
    try:
        material_service = MaterialService(db)
        result = material_service.upload_material(
            material_data=material_data,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{material_id}",
    response_model=MaterialResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Update material",
    description="Update a course material (teacher or admin).",
)
def update_material(
    material_id: int,
    update_data: MaterialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a course material.
    
    **Teacher or Admin only.**
    
    - **material_id**: Material ID
    - **title**: Material title
    - **description**: Material description
    - **is_published**: Publish status
    """
    try:
        material_service = MaterialService(db)
        result = material_service.update_material(
            material_id=material_id,
            update_data=update_data,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Delete material",
    description="Delete a course material (teacher or admin).",
)
def delete_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a course material.
    
    **Teacher or Admin only.**
    
    - **material_id**: Material ID
    """
    try:
        material_service = MaterialService(db)
        material_service.delete_material(
            material_id=material_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{material_id}/publish",
    response_model=MaterialResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Publish material",
    description="Publish a course material (teacher or admin).",
)
def publish_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Publish a course material.
    
    **Teacher or Admin only.**
    
    - **material_id**: Material ID
    """
    try:
        material_service = MaterialService(db)
        result = material_service.publish_material(
            material_id=material_id,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{material_id}/unpublish",
    response_model=MaterialResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Unpublish material",
    description="Unpublish a course material (teacher or admin).",
)
def unpublish_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Unpublish a course material.
    
    **Teacher or Admin only.**
    
    - **material_id**: Material ID
    """
    try:
        material_service = MaterialService(db)
        result = material_service.unpublish_material(
            material_id=material_id,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: MATERIAL STATISTICS
# ============================================================

@router.get(
    "/stats/{course_id}",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get material statistics",
    description="Get material statistics for a course (admin).",
)
def get_material_stats(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get material statistics for a course.
    
    **Admin only.**
    
    - **course_id**: Course ID
    """
    try:
        material_service = MaterialService(db)
        stats = material_service.get_material_stats(
            course_id=course_id,
            user_id=current_user.id,
        )
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )