# ============================================================
# AETHER LINK - USERS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Any
import base64
import re

from ...core.database import get_db
from ...core.dependencies import get_current_user, get_current_admin_user, rate_limiter
from ...services.user_service import UserService
from ...services.auth_service import AuthService
from ...schemas.user import (
    UserResponse,
    UserUpdate,
    UserRoleUpdate,
    UserListResponse,
    UserStatusUpdate,
)
from ...models.user import User, UserRole

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================
# CURRENT USER PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get current user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the current user's profile.
    """
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Update current user profile",
)
def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update the current user's profile.
    
    - **full_name**: 1-100 characters
    - **phone**: Valid phone number format
    - **bio**: Max 500 characters
    - **profile_picture**: Valid URL
    """
    try:
        user_service = UserService(db)
        updated_user = user_service.update_profile(
            user_id=current_user.id,
            update_data=update_data,
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# UPDATE PROFILE PICTURE - FIXED: Accepts base64 or URL
# ============================================================

@router.put(
    "/me/picture",
    response_model=UserResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Update profile picture",
)
async def update_profile_picture(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update the current user's profile picture.
    
    Accepts:
    - JSON: {"picture_url": "https://..."} 
    - JSON: {"picture_url": "data:image/png;base64,..."}
    - Form data with file upload (future)
    """
    try:
        import json

        # Get the request body (await bytes)
        raw = await request.body()
        try:
            data = json.loads(raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else raw)
            picture_url = data.get("picture_url")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body. Expected: {\"picture_url\": \"...\"}"
            )
        
        if not picture_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="picture_url is required"
            )
        
        # Validate URL format
        if not picture_url.startswith(('http://', 'https://', 'data:image')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="picture_url must be a valid URL or base64 image"
            )
        
        user_service = UserService(db)
        updated_user = user_service.update_profile_picture(
            user_id=current_user.id,
            picture_url=picture_url,
        )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile picture: {str(e)}",
        )


# ============================================================
# ALTERNATIVE: Upload profile picture with file
# ============================================================

@router.post(
    "/me/picture/upload",
    response_model=UserResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Upload profile picture (file upload)",
)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload a profile picture as a file.
    
    Supports: PNG, JPG, JPEG, WebP
    Max size: 5MB
    """
    try:
        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Validate file size (5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        # Convert to base64 for storage
        import base64
        base64_image = base64.b64encode(contents).decode('utf-8')
        picture_url = f"data:{file.content_type};base64,{base64_image}"
        
        user_service = UserService(db)
        updated_user = user_service.update_profile_picture(
            user_id=current_user.id,
            picture_url=picture_url,
        )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading picture: {str(e)}",
        )


# ============================================================
# ADMIN ONLY: USER MANAGEMENT
# ============================================================

@router.get(
    "/",
    response_model=UserListResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get all users (admin only)",
)
def get_users(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    role: Optional[str] = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Only active users"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all users with pagination and filters.
    
    **Admin only.**
    
    - **skip**: Number of users to skip
    - **limit**: Max users to return (1-100)
    - **role**: Filter by role (student, teacher, admin)
    - **active_only**: Only include active users
    - **search**: Search by name or email
    """
    try:
        user_service = UserService(db)
        
        # Convert role string to enum
        role_enum = None
        if role:
            try:
                role_enum = UserRole(role.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}. Must be student, teacher, or admin",
                )
        
        result = user_service.get_users(
            skip=skip,
            limit=limit,
            role=role_enum,
            active_only=active_only,
            search=search,
        )
        
        return {
            "users": result["users"],
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
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Get user by ID (admin only)",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by ID.
    
    **Admin only.**
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user_profile(user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Update user role (admin only)",
)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a user's role.
    
    **Admin only.**
    
    - **role**: student, teacher, or admin
    """
    try:
        user_service = UserService(db)
        user = user_service.update_role(
            user_id=user_id,
            role_data=role_data,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{user_id}/activate",
    response_model=UserResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Activate user account (admin only)",
)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Activate a user account.
    
    **Admin only.**
    """
    try:
        user_service = UserService(db)
        user = user_service.activate_user(user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    dependencies=[Depends(get_current_admin_user)],
    summary="Deactivate user account (admin only)",
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Deactivate a user account.
    
    **Admin only.**
    """
    try:
        user_service = UserService(db)
        user = user_service.deactivate_user(user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin_user)],
    summary="Delete user (admin only)",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Soft delete a user.
    
    **Admin only.**
    
    - Cannot delete self
    - Cannot delete users with active courses or enrollments
    """
    try:
        user_service = UserService(db)
        user_service.delete_user(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )