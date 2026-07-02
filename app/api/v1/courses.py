# ============================================================
# AETHER LINK - COURSES API
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
from ...services.course_service import CourseService
from ...services.user_service import UserService
from ...schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/courses", tags=["Courses"])


# ============================================================
# PUBLIC ENDPOINTS
# ============================================================

@router.get(
    "/",
    response_model=CourseListResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get published courses",
    description="Get published courses with pagination and optional featured filter.",
)
def get_courses(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit (max 100)"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get published courses with optional filtering.
    
    - **skip**: Number of courses to skip
    - **limit**: Max courses to return (1-100)
    - **featured**: Filter by featured status (true/false)
    """
    try:
        course_service = CourseService(db)
        result = course_service.get_published_courses(
            skip=skip,
            limit=limit,
            featured=featured,
        )
        
        return {
            "courses": result["courses"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/search",
    dependencies=[Depends(rate_limiter)],
    summary="Search courses",
    description="Search courses by title or description.",
)
def search_courses(
    q: str = Query(..., min_length=2, description="Search query"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Search courses by title or description.
    
    - **q**: Search query (minimum 2 characters)
    """
    try:
        course_service = CourseService(db)
        courses = course_service.search_courses(query=q)
        return courses
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get course by ID",
    description="Get course details with sessions.",
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a course by ID with all details.
    
    - **course_id**: Course ID
    """
    try:
        course_service = CourseService(db)
        course = course_service.get_course_with_details(course_id)
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# TEACHER/ADMIN ENDPOINTS
# ============================================================

@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Create a course",
    description="Create a new course (teacher or admin only).",
)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new course.
    
    **Teacher or Admin only.**
    
    - **title**: 3-255 characters
    - **slug**: 3-100 characters, a-z0-9-
    - **price**: 0-999,999 PKR
    - **status**: draft, published, archived
    """
    try:
        course_service = CourseService(db)
        course = course_service.create_course(
            course_data=course_data,
            teacher_id=current_user.id,
        )
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Update a course",
    description="Update an existing course (teacher or admin only).",
)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update an existing course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - **title**: 3-255 characters
    - **slug**: 3-100 characters, a-z0-9-
    - **price**: 0-999,999 PKR
    - **status**: draft, published, archived
    """
    try:
        course_service = CourseService(db)
        course = course_service.update_course(
            course_id=course_id,
            update_data=course_data,
            user_id=current_user.id,
        )
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limiter)],
    summary="Delete a course",
    description="Soft delete a course (teacher or admin only).",
)
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - Cannot delete with active enrollments
    """
    try:
        course_service = CourseService(db)
        course_service.delete_course(
            course_id=course_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{course_id}/publish",
    response_model=CourseResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Publish a course",
    description="Publish a course (teacher or admin only).",
)
def publish_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Publish a course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - Course must have at least one session
    """
    try:
        course_service = CourseService(db)
        course = course_service.publish_course(
            course_id=course_id,
            user_id=current_user.id,
        )
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{course_id}/archive",
    response_model=CourseResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Archive a course",
    description="Archive a course (teacher or admin only).",
)
def archive_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Archive a course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - Cannot archive with active enrollments
    """
    try:
        course_service = CourseService(db)
        course = course_service.archive_course(
            course_id=course_id,
            user_id=current_user.id,
        )
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{course_id}/featured",
    response_model=CourseResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Toggle featured status",
    description="Toggle featured status of a course (teacher or admin only).",
)
def toggle_featured(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Toggle featured status of a course.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    """
    try:
        course_service = CourseService(db)
        course = course_service.toggle_featured(
            course_id=course_id,
            user_id=current_user.id,
        )
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/teacher/{teacher_id}",
    response_model=List[CourseResponse],
    dependencies=[Depends(rate_limiter)],
    summary="Get teacher's courses",
    description="Get all courses for a specific teacher.",
)
def get_teacher_courses(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all courses for a specific teacher.
    
    - **teacher_id**: Teacher ID
    """
    try:
        course_service = CourseService(db)
        courses = course_service.get_courses_by_teacher(teacher_id)
        return courses
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )