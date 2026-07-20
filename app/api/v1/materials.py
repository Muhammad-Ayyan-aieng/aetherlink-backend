# ============================================================
# AETHER LINK - MATERIALS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, File, UploadFile, Form
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
    MaterialTypeEnum,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/materials", tags=["Materials"])


# ============================================================
# HELPER: Convert MaterialTypeEnum to string for Form
# ============================================================

def validate_file_type(file_type: str) -> str:
    """Validate file type is allowed."""
    allowed = [t.value for t in MaterialTypeEnum]
    if file_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed)}"
        )
    return file_type


# ============================================================
# PUBLIC: SEARCH (MUST BE FIRST - BEFORE ANY VARIABLE ROUTES)
# ============================================================

@router.get(
    "/search",
    dependencies=[Depends(rate_limiter)],
    summary="Search materials",
    description="Search course materials. Public access - no authentication required.",
)
def search_materials(
    q: str = Query(..., min_length=1, description="Search query"),
    course_id: Optional[int] = Query(None, description="Filter by course"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Search materials by title or description.
    
    **Public access - no authentication required.**
    """
    try:
        if not q or len(q.strip()) < 1:
            return []
        
        material_service = MaterialService(db)
        
        results = material_service.search_materials_public(
            query=q.strip(),
            course_id=course_id,
            file_type=file_type,
        )
        return results
    except ValueError as e:
        return []


# ============================================================
# PUBLIC: COURSE MATERIALS (MUST BE BEFORE /{material_id})
# ============================================================

@router.get(
    "/course/{course_id}",
    response_model=MaterialListResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get course materials",
    description="Get all materials for a course. Public access - no authentication required.",
)
def get_course_materials(
    course_id: int,
    published_only: bool = Query(True, description="Only published materials"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get materials for a course.
    
    **Public access - no authentication required.**
    """
    try:
        material_service = MaterialService(db)
        course_service = CourseService(db)
        
        course = course_service.get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        
        result = material_service.get_course_materials_public(
            course_id=course_id,
            published_only=True,
            skip=skip,
            limit=limit,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# ENROLLED STUDENT: COURSE MATERIALS (MUST BE BEFORE /{material_id})
# ============================================================

@router.get(
    "/enrolled/course/{course_id}",
    response_model=MaterialListResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get course materials (enrolled)",
    description="Get all materials for a course including unpublished (requires enrollment).",
)
def get_enrolled_course_materials(
    course_id: int,
    published_only: bool = Query(False, description="Only published materials"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_teacher_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get materials for a course.
    
    **Requires authentication and enrollment.**
    """
    try:
        material_service = MaterialService(db)
        enrollment_service = EnrollmentService(db)
        course_service = CourseService(db)
        
        course = course_service.get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        
        is_enrolled = enrollment_service.is_enrolled(current_user.id, course_id)
        is_teacher = course.teacher_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN
        
        if not is_enrolled and not is_teacher and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled in this course to view materials",
            )
        
        can_view_unpublished = is_teacher or is_admin
        
        result = material_service.get_course_materials(
            course_id=course_id,
            user_id=current_user.id,
            published_only=published_only if can_view_unpublished else True,
            skip=skip,
            limit=limit,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# TEACHER: MY COURSE MATERIALS (MUST BE BEFORE /{material_id})
# ============================================================

@router.get(
    "/teacher/my-courses",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get my course materials",
    description="Get all materials for courses taught by the current teacher.",
)
def get_teacher_materials(
    published_only: bool = Query(False, description="Only published materials"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    current_user: User = Depends(get_current_teacher_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all materials for courses taught by the current teacher.
    
    **Teacher only.**
    """
    try:
        material_service = MaterialService(db)
        course_service = CourseService(db)
        
        courses = course_service.get_teacher_courses(current_user.id)
        course_ids = [c.id for c in courses]
        
        if not course_ids:
            return {
                "materials": [],
                "total": 0,
                "page": 1,
                "page_size": limit,
                "total_pages": 0,
            }
        
        all_materials = []
        for course_id in course_ids:
            materials = material_service.get_course_materials(
                course_id=course_id,
                user_id=current_user.id,
                published_only=published_only,
                skip=0,
                limit=1000,
            )
            all_materials.extend(materials["materials"])
        
        total = len(all_materials)
        paginated = all_materials[skip:skip + limit]
        
        return {
            "materials": paginated,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: MATERIAL STATISTICS (MUST BE BEFORE /{material_id})
# ============================================================

@router.get(
    "/stats/{course_id}",
    dependencies=[Depends(get_current_admin_user)],
    summary="Get material statistics",
    description="Get material statistics for a course (admin).",
)
def get_material_stats(
    course_id: int,
    current_user: User = Depends(get_current_teacher_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get material statistics for a course.
    
    **Admin only.**
    """
    try:
        material_service = MaterialService(db)
        course_service = CourseService(db)
        
        course = course_service.get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        
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


# ============================================================
# GET MATERIAL BY ID (Public + Authenticated)
# ============================================================

@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get material by ID",
    description="Get a course material by ID. Returns signed URL if authenticated and authorized.",
)
def get_material(
    material_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a material by ID.
    
    **Public access** - returns only published materials without signed URL.
    **Authenticated** - returns signed URL if user is enrolled, teacher, or admin.
    """
    try:
        material_service = MaterialService(db)
        
        # Check if user is authenticated
        if current_user:
            # Check if user is enrolled, teacher, or admin
            material = material_service.material_repo.get_by_id(material_id)
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Material not found",
                )
            
            # Check enrollment or authorization
            course = material.course
            is_enrolled = False
            if current_user.role == UserRole.STUDENT:
                enrollment_service = EnrollmentService(db)
                is_enrolled = enrollment_service.is_enrolled(current_user.id, material.course_id)
            
            is_teacher = course.teacher_id == current_user.id
            is_admin = current_user.role == UserRole.ADMIN
            
            if is_enrolled or is_teacher or is_admin:
                # Get material with signed URL
                result = material_service.get_material(
                    material_id=material_id,
                    user_id=current_user.id,
                )
                return result
        
        # Public access or not authorized - only published materials, no signed URL
        result = material_service.get_material_public(
            material_id=material_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN: UPLOAD MATERIAL (WITH FILE)
# ============================================================

@router.post(
    "/",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Upload material",
    description="Upload a course material with file (teacher or admin).",
)
async def upload_material(
    course_id: int = Form(..., description="Course ID"),
    title: str = Form(..., min_length=3, max_length=255, description="Material title"),
    description: Optional[str] = Form(None, max_length=1000, description="Material description"),
    file_type: str = Form(..., description="File type: pdf, pptx, doc, docx, link"),
    file: Optional[UploadFile] = File(None, description="File to upload (for file types)"),
    link_url: Optional[str] = Form(None, description="Link URL (for link type)"),
    current_user: User = Depends(get_current_teacher_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload a course material with file.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - **title**: Material title
    - **file_type**: pdf, pptx, doc, docx, link
    - **file**: File upload (for file types)
    - **link_url**: URL (for link type)
    """
    try:
        # Validate file type
        validate_file_type(file_type)
        
        # Create material data
        material_data = MaterialUpload(
            course_id=course_id,
            title=title,
            description=description,
            file_type=MaterialTypeEnum(file_type),
            link_url=link_url,
        )
        
        material_service = MaterialService(db)
        result = await material_service.upload_material(
            material_data=material_data,
            file=file,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload material: {str(e)}",
        )


# ============================================================
# TEACHER/ADMIN: UPDATE MATERIAL
# ============================================================

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
    current_user: User = Depends(get_current_teacher_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a course material.
    
    **Teacher or Admin only.**
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


# ============================================================
# TEACHER/ADMIN: DELETE MATERIAL
# ============================================================

@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Delete material",
    description="Delete a course material (teacher or admin).",
)
def delete_material(
    material_id: int,
    current_user: User = Depends(get_current_teacher_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a course material.
    
    **Teacher or Admin only.**
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


# ============================================================
# TEACHER/ADMIN: PUBLISH MATERIAL
# ============================================================

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


# ============================================================
# TEACHER/ADMIN: UNPUBLISH MATERIAL
# ============================================================

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