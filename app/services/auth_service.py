# ============================================================
# AETHER LINK - AUTHENTICATION SERVICE
# ============================================================

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import secrets
import string

from ..repositories.user_repository import UserRepository
from ..repositories.invitation_repository import InvitationRepository
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    validate_password_strength,
)
from ..repositories.refresh_token_repository import RefreshTokenRepository
import hashlib
import secrets
from datetime import timedelta
from ..models.user import User, UserRole
from ..schemas.auth import UserRegister, UserLogin, PasswordChange
from ..utils.sanitizer import sanitize_text, sanitize_email, sanitize_username
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.invitation_repo = InvitationRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
    
    # ============================================================
    # REGISTER - Teachers active, Students inactive
    # ============================================================
    
    def register(self, user_data: UserRegister) -> Dict[str, Any]:
        """
        Register a new user.
        
        - Teachers (from invitation): Account is ACTIVE immediately
        - Students (from application): Account is INACTIVE until admin approval
        
        Args:
            user_data: Registration data
            
        Returns:
            Created user or error
            
        Raises:
            ValueError: If validation fails
        """
        # Sanitize all user inputs (XSS prevention)
        email = sanitize_email(user_data.email)
        username = sanitize_username(user_data.username)
        full_name = sanitize_text(user_data.full_name.strip(), max_length=100)
        phone = sanitize_text(user_data.phone.strip(), max_length=20) if user_data.phone else None
        
        # Validate required fields after sanitization
        if not email:
            raise ValueError("Valid email is required")
        if not username:
            raise ValueError("Valid username is required")
        if not full_name:
            raise ValueError("Full name is required")
        
        # Check if email is taken (using sanitized email)
        if self.user_repo.is_email_taken(email):
            raise ValueError("Email already registered")
        
        # Check if username is taken (using sanitized username)
        if self.user_repo.is_username_taken(username):
            raise ValueError("Username already taken")
        
        # Validate password strength
        password_check = validate_password_strength(user_data.password)
        if not password_check["is_strong"]:
            raise ValueError(f"Password too weak: {', '.join(password_check['errors'])}")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # ============================================================
        # Determine if user should be active immediately
        # Teachers from invitations are active, students need approval
        # ============================================================
        
        # Check if this is a teacher invitation
        is_teacher_invitation = self._is_teacher_invitation(email)
        
        # Create user
        user = self.user_repo.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            phone=phone,
            role=UserRole.STUDENT,  # Default role
            is_verified=False,
            is_active=is_teacher_invitation,  # Active only if teacher invitation
        )
        
        # If this is a teacher invitation, update role to teacher
        if is_teacher_invitation:
            user.role = UserRole.TEACHER
            self.db.commit()
            self.db.refresh(user)
            
            return {
                "user": user,
                "message": "Teacher account created successfully!",
                "requires_approval": False,
            }
        
        # Student registration (requires approval)
        return {
            "user": user,
            "message": "Registration successful. Your account is pending approval. You will receive an email once verified.",
            "requires_approval": True,
        }
    
    def _is_teacher_invitation(self, email: str) -> bool:
        """
        Check if the email has a pending teacher invitation.
        
        Args:
            email: Email to check
            
        Returns:
            True if there's a pending teacher invitation
        """
        # Check for pending invitation
        invitation = self.invitation_repo.get_pending_by_email(email)
        return invitation is not None
    
    # ============================================================
    # LOGIN - Check is_active
    # ============================================================
    
    def login(self, login_data: UserLogin) -> Dict[str, Any]:
        """
        Login a user.
        
        Checks if user is active before allowing login.
        
        Args:
            login_data: Login credentials
            
        Returns:
            Tokens and user info
            
        Raises:
            ValueError: If credentials invalid or account inactive
        """
        # Sanitize email
        email = sanitize_email(login_data.email)
        
        if not email:
            raise ValueError("Invalid email format")
        
        # Find user by email
        user = self.user_repo.get_by_email(email)
        
        # Generic error to prevent enumeration
        if not user:
            raise ValueError("Invalid email or password")
        
        # ============================================================
        # Check if user is active before login
        # ============================================================
        if not user.is_active:
            raise ValueError(
                "Your account is pending approval. "
                "Please wait for admin verification or contact support."
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        # Update last login
        self.user_repo.update_last_login(user.id)
        
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        
        access_token = create_access_token(token_data)

        # Generate opaque refresh token and store its hash
        refresh_token_str = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(days=7)
        self.refresh_token_repo.create(
            user_id=user.id,
            token_str=refresh_token_str,
            expires_at=expires_at,
            ip_address=None,
            user_agent=None,
        )

        logger.info("Issued refresh token for user_id=%s", user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "expires_in": 60 * 60,  # 1 hour
        }
    
    # ============================================================
    # ACTIVATE USER (Admin Only)
    # ============================================================
    
    def activate_user(self, user_id: int, admin_id: int) -> Dict[str, Any]:
        """
        Activate a user account (Admin only).
        
        Args:
            user_id: User ID to activate
            admin_id: Admin ID who is activating
            
        Returns:
            Success message
            
        Raises:
            ValueError: If user not found or already active
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.is_active:
            raise ValueError("User is already active")
        
        # Activate user
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        
        # TODO: Send email notification to user
        # TODO: Log activation in audit trail
        
        return {
            "message": f"User {user.email} has been activated successfully",
            "user_id": user.id,
        }
    
    # ============================================================
    # DEACTIVATE USER (Admin Only)
    # ============================================================
    
    def deactivate_user(self, user_id: int, admin_id: int) -> Dict[str, Any]:
        """
        Deactivate a user account (Admin only).
        
        Args:
            user_id: User ID to deactivate
            admin_id: Admin ID who is deactivating
            
        Returns:
            Success message
            
        Raises:
            ValueError: If user not found or already inactive
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not user.is_active:
            raise ValueError("User is already inactive")
        
        # Deactivate user
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        
        return {
            "message": f"User {user.email} has been deactivated",
            "user_id": user.id,
        }
    
    # ============================================================
    # REFRESH TOKEN
    # ============================================================
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New tokens
            
        Raises:
            ValueError: If refresh token invalid
        """
        # Treat refresh_token as opaque token string; look up by hash
        token_record = self.refresh_token_repo.get_by_hash(refresh_token)
        if not token_record:
            raise ValueError("Invalid refresh token")

        # Check expiration and revocation
        if token_record.revoked:
            # Possible token reuse - revoke all tokens for this user
            self.refresh_token_repo.revoke_all_for_user(token_record.user_id)
            raise ValueError("Refresh token revoked")

        if token_record.expires_at < datetime.utcnow():
            raise ValueError("Refresh token expired")

        user = self.user_repo.get_by_id(token_record.user_id)
        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User account is inactive")

        # Rotate: create new refresh token and revoke old one
        new_refresh_token_str = secrets.token_urlsafe(64)
        new_expires = datetime.utcnow() + timedelta(days=7)
        new_record = self.refresh_token_repo.create(
            user_id=user.id,
            token_str=new_refresh_token_str,
            expires_at=new_expires,
            ip_address=None,
            user_agent=None,
        )

        # Mark old token revoked and link to new
        self.refresh_token_repo.mark_replaced(token_record, new_record)

        logger.info(
            "Rotated refresh token for user_id=%s; old_token_id=%s replaced_by=%s",
            user.id,
            getattr(token_record, 'id', token_record.get('id') if isinstance(token_record, dict) else None),
            getattr(new_record, 'id', new_record.get('id') if isinstance(new_record, dict) else None),
        )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }

        new_access_token = create_access_token(token_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
            "expires_in": 60 * 60,
        }

    def revoke_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Revoke a specific refresh token (by opaque token string).
        """
        token_record = self.refresh_token_repo.get_by_hash(refresh_token)
        if not token_record:
            raise ValueError("Invalid refresh token")
        self.refresh_token_repo.revoke(token_record)
        logger.info("Revoked refresh token for user_id=%s, token_id=%s",
                    getattr(token_record, 'user_id', token_record.get('user_id') if isinstance(token_record, dict) else None),
                    getattr(token_record, 'id', token_record.get('id') if isinstance(token_record, dict) else None))
        return {"message": "Refresh token revoked"}

    def revoke_all_tokens_for_user(self, user_id: int) -> Dict[str, Any]:
        """
        Revoke all active refresh tokens for a user.
        """
        count = self.refresh_token_repo.revoke_all_for_user(user_id)
        logger.info("Revoked all refresh tokens for user_id=%s, count=%s", user_id, count)
        return {"message": f"Revoked {count} refresh tokens"}
    
    # ============================================================
    # CHANGE PASSWORD
    # ============================================================
    
    def change_password(
        self, 
        user_id: int, 
        password_data: PasswordChange
    ) -> Dict[str, Any]:
        """
        Change user password.
        
        Args:
            user_id: User ID
            password_data: Old and new password
            
        Returns:
            Success message
            
        Raises:
            ValueError: If old password incorrect or new password weak
        """
        user = self.user_repo.get_by_id_or_fail(user_id)
        
        # Verify old password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise ValueError("Incorrect current password")
        
        # Check if same as old password
        if verify_password(password_data.new_password, user.hashed_password):
            raise ValueError("New password must be different from current")
        
        # Validate new password strength
        password_check = validate_password_strength(password_data.new_password)
        if not password_check["is_strong"]:
            raise ValueError(f"Password too weak: {', '.join(password_check['errors'])}")
        
        # Hash and update
        user.hashed_password = get_password_hash(password_data.new_password)
        self.db.commit()
        
        return {"message": "Password changed successfully"}
    
    # ============================================================
    # RESET PASSWORD (Request)
    # ============================================================
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset.
        
        Args:
            email: User email
            
        Returns:
            Success message (always generic for security)
        """
        # Sanitize email
        sanitized_email = sanitize_email(email)
        
        if not sanitized_email:
            return {"message": "If an account exists, a reset link will be sent"}
        
        user = self.user_repo.get_by_email(sanitized_email)
        
        # Always return same message for security (prevent email enumeration)
        if not user:
            return {"message": "If an account exists, a reset link will be sent"}
        
        # TODO: Generate reset token and send email
        
        return {
            "message": "If an account exists, a reset link will be sent",
        }
    
    # ============================================================
    # RESET PASSWORD (Confirm)
    # ============================================================
    
    def confirm_password_reset(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Confirm password reset with token.
        
        Args:
            token: Reset token
            new_password: New password
            
        Returns:
            Success message
            
        Raises:
            ValueError: If token invalid or expired
        """
        # TODO: Validate reset token and find user
        
        # Validate new password strength
        password_check = validate_password_strength(new_password)
        if not password_check["is_strong"]:
            raise ValueError(f"Password too weak: {', '.join(password_check['errors'])}")
        
        # TODO: Update user password and invalidate token
        
        return {"message": "Password reset successfully"}
    
    # ============================================================
    # VERIFY EMAIL
    # ============================================================
    
    def verify_email(self, token: str) -> Dict[str, Any]:
        """
        Verify user email.
        
        Args:
            token: Verification token
            
        Returns:
            Success message
            
        Raises:
            ValueError: If token invalid or expired
        """
        # TODO: Validate verification token and find user
        
        return {"message": "Email verified successfully"}
    
    # ============================================================
    # GET CURRENT USER
    # ============================================================
    
    def get_current_user(self, token: str) -> User:
        """
        Get current user from token.
        
        Args:
            token: JWT token
            
        Returns:
            User
            
        Raises:
            ValueError: If token invalid or user not found
        """
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")
            
            user = self.user_repo.get_by_id(int(user_id))
            if not user:
                raise ValueError("User not found")
            
            if not user.is_active:
                raise ValueError("User account is inactive")
            
            return user
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    # ============================================================
    # VALIDATE TOKEN
    # ============================================================
    
    def validate_token(self, token: str) -> bool:
        """
        Validate JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            True if valid
        """
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            if not user_id:
                return False
            
            user = self.user_repo.get_by_id(int(user_id))
            if not user or not user.is_active:
                return False
            
            return True
        except Exception:
            return False
    
    # ============================================================
    # ADMIN: CREATE TEACHER ACCOUNT
    # ============================================================
    
    def create_teacher_from_invitation(self, token: str, password: str, username: str) -> User:
        """
        Create teacher account from invitation.
        
        Args:
            token: Invitation token
            password: New password
            username: New username
            
        Returns:
            Created user
            
        Raises:
            ValueError: If invitation invalid or expired
        """
        # Get valid invitation
        invitation = self.invitation_repo.get_valid_token(token)
        if not invitation:
            raise ValueError("Invalid or expired invitation token")
        
        # Sanitize inputs
        sanitized_username = sanitize_username(username)
        sanitized_email = sanitize_email(invitation.email)
        
        # Check if email already registered
        if self.user_repo.is_email_taken(sanitized_email):
            raise ValueError("Email already registered")
        
        # Check if username taken
        if self.user_repo.is_username_taken(sanitized_username):
            raise ValueError("Username already taken")
        
        # Validate password strength
        password_check = validate_password_strength(password)
        if not password_check["is_strong"]:
            raise ValueError(f"Password too weak: {', '.join(password_check['errors'])}")
        
        # Create teacher user (active by default since they were invited)
        hashed_password = get_password_hash(password)
        user = self.user_repo.create(
            email=sanitized_email,
            username=sanitized_username,
            hashed_password=hashed_password,
            full_name=invitation.full_name,
            phone=invitation.phone,
            role=UserRole.TEACHER,
            is_verified=True,
            is_active=True,  # Teachers are active immediately
        )
        
        # Mark invitation as accepted
        self.invitation_repo.accept_invitation(token)
        
        return user