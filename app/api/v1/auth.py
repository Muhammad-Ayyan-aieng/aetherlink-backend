# ============================================================
# AETHER LINK - AUTHENTICATION API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
import json

from ...core.database import get_db
from ...core.dependencies import rate_limiter, auth_rate_limiter, get_current_user, get_current_admin_user
from ...services.auth_service import AuthService
from ...services.user_service import UserService
from ...models.user import User
from ...schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshToken,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    LogoutResponse,
)
from ...schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# REGISTER - DISABLED (Use Application Flow Instead)
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    summary="Registration is disabled",
    description="Registration is only available through course applications.",
)
def register_disabled():
    """
    Registration is disabled.
    
    Please apply for a course through the application process.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Registration is only available through course applications. Please apply for a course to create an account.",
    )


# ============================================================
# LOGIN - UPDATED: Better inactive account message
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(auth_rate_limiter)],
    summary="Login with email and password",
    description="Authenticate user and return access and refresh tokens. Supports both JSON and form data.",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Login with email and password.
    
    Supports both:
    - JSON: {"email": "...", "password": "..."}
    - Form: username=...&password=...
    """
    try:
        # Try to parse as JSON first
        body = await request.body()
        login_data = None
        
        if body:
            try:
                data = json.loads(body)
                if "email" in data or "username" in data:
                    email = data.get("email") or data.get("username", "")
                    password = data.get("password", "")
                    
                    if not email or not password:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Email and password are required"
                        )
                    
                    login_data = UserLogin(email=email, password=password)
            except json.JSONDecodeError:
                pass
        
        # If JSON parsing failed, try form data
        if not login_data:
            form = await request.form()
            if form:
                email = form.get("username", "")
                password = form.get("password", "")
                
                if not email or not password:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Email and password are required"
                    )
                
                login_data = UserLogin(email=email, password=password)
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Email and password are required"
                )
        
        auth_service = AuthService(db)
        result = auth_service.login(login_data)
        
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "username": result["user"].username,
                "full_name": result["user"].full_name,
                "role": result["user"].role.value,
                "is_active": result["user"].is_active,
            },
        }
    except HTTPException:
        raise
    except ValueError as e:
        # Better error message for inactive accounts
        error_msg = str(e)
        if "pending approval" in error_msg.lower() or "inactive" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": error_msg,
                    "code": "ACCOUNT_INACTIVE",
                    "requires_approval": True,
                }
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


# ============================================================
# LOGIN WITH JSON (DEPRECATED - USE /login INSTEAD)
# ============================================================

@router.post(
    "/login/email",
    response_model=TokenResponse,
    dependencies=[Depends(auth_rate_limiter)],
    summary="Login with email and password (JSON)",
    description="Authenticate user with JSON body. Use /login instead for both formats.",
)
def login_email(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Login with email and password using JSON body.
    
    - **email**: Your email address
    - **password**: Your password
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.login(login_data)
        
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "username": result["user"].username,
                "full_name": result["user"].full_name,
                "role": result["user"].role.value,
                "is_active": result["user"].is_active,
            },
        }
    except ValueError as e:
        error_msg = str(e)
        if "pending approval" in error_msg.lower() or "inactive" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": error_msg,
                    "code": "ACCOUNT_INACTIVE",
                    "requires_approval": True,
                }
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
        )


# ============================================================
# REFRESH TOKEN
# ============================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token.",
)
def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db),
) -> Any:
    """
    Refresh access token.
    
    - **refresh_token**: Your refresh token
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.refresh_token(refresh_data.refresh_token)
        
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
    description="Logout the current user (client-side token removal).",
)
def logout() -> Any:
    """
    Logout the current user.
    
    Since JWT tokens are stateless, logout is handled client-side
    by removing the token. This endpoint exists for convenience.
    """
    return LogoutResponse(message="Successfully logged out. Please remove the token client-side.")


@router.post(
    "/revoke-refresh",
    summary="Revoke a refresh token",
    description="Revoke a single refresh token (opaque token string).",
)
def revoke_refresh(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db),
) -> Any:
    try:
        auth_service = AuthService(db)
        result = auth_service.revoke_refresh_token(refresh_data.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/revoke-all",
    summary="Revoke all refresh tokens for current user",
    description="Revoke all active refresh tokens for the authenticated user.",
)
def revoke_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    auth_service = AuthService(db)
    return auth_service.revoke_all_tokens_for_user(current_user.id)


# ============================================================
# GET CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the currently authenticated user's profile.",
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the current user's profile.
    
    Requires authentication via Bearer token.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "profile_picture": current_user.profile_picture,
        "bio": current_user.bio,
        "role": current_user.role.value,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post(
    "/change-password",
    summary="Change password",
    description="Change the current user's password.",
)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Change the current user's password.
    
    Requires authentication via Bearer token.
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.change_password(current_user.id, password_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post(
    "/forgot-password",
    dependencies=[Depends(auth_rate_limiter)],
    summary="Request password reset",
    description="Send a password reset link to the user's email.",
)
def forgot_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db),
) -> Any:
    """
    Request a password reset link.
    
    - **email**: Your email address
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.request_password_reset(reset_data.email)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
    dependencies=[Depends(auth_rate_limiter)],
    summary="Confirm password reset",
    description="Reset password using the reset token.",
)
def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> Any:
    """
    Confirm password reset with token.
    
    - **token**: Reset token from email
    - **new_password**: Your new password
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.confirm_password_reset(
            token=reset_data.token,
            new_password=reset_data.new_password,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: ACTIVATE USER
# ============================================================

@router.put(
    "/admin/activate/{user_id}",
    dependencies=[Depends(get_current_admin_user)],
    summary="Activate user account (Admin only)",
    description="Activate a user account. Admin only.",
)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Activate a user account.
    
    **Admin only.**
    
    - **user_id**: ID of user to activate
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.activate_user(user_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ADMIN: DEACTIVATE USER
# ============================================================

@router.put(
    "/admin/deactivate/{user_id}",
    dependencies=[Depends(get_current_admin_user)],
    summary="Deactivate user account (Admin only)",
    description="Deactivate a user account. Admin only.",
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Deactivate a user account.
    
    **Admin only.**
    
    - **user_id**: ID of user to deactivate
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.deactivate_user(user_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )