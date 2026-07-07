# ============================================================
# AETHER LINK - EMAIL SERVICE
# ============================================================

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.email import get_email_client
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.client = get_email_client()
        self.from_email = settings.EMAIL_FROM
        self.app_name = settings.APP_NAME
        self.app_url = "https://lms.aetherlink.com"  # Update with your domain
    
    # ============================================================
    # APPLICATION EMAILS
    # ============================================================
    
    async def send_application_confirmation(self, email: str, full_name: str, course_title: str) -> bool:
        """
        Send application confirmation email to student.
        
        Args:
            email: Student email
            full_name: Student full name
            course_title: Course title
            
        Returns:
            True if sent successfully
        """
        subject = f"Application Received - {self.app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{self.app_name}</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>Thank you for applying to <strong>{course_title}</strong>.</p>
                    <p>Your application has been received and is currently under review by our team.</p>
                    <p>We will notify you once a decision has been made. This typically takes 1-2 business days.</p>
                    <p>If you have any questions, please contact us at {self.from_email}.</p>
                    <br>
                    <p>Best regards,</p>
                    <p><strong>{self.app_name} Team</strong></p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {self.app_name}. All rights reserved.</p>
                    <p>You are receiving this email because you submitted an application.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.client.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_application_approved(
        self,
        email: str,
        full_name: str,
        course_title: str,
        username: str,
        password: str
    ) -> bool:
        """
        Send application approval email with credentials.
        
        Args:
            email: Student email
            full_name: Student full name
            course_title: Course title
            username: Generated username
            password: Generated password
            
        Returns:
            True if sent successfully
        """
        subject = f"Application Approved - {self.app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10B981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .credentials {{ background: #F3F4F6; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                .button {{ background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
                .warning {{ color: #DC2626; font-size: 14px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Application Approved!</h1>
                </div>
                <div class="content">
                    <h2>Congratulations {full_name}!</h2>
                    <p>Your application for <strong>{course_title}</strong> has been approved.</p>
                    
                    <p>You can now access the LMS using the following credentials:</p>
                    
                    <div class="credentials">
                        <p><strong>Login URL:</strong> <a href="{self.app_url}">{self.app_url}</a></p>
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>Password:</strong> <code>{password}</code></p>
                    </div>
                    
                    <p class="warning">⚠️ Please change your password after your first login.</p>
                    
                    <p>
                        <a href="{self.app_url}" class="button">Go to LMS</a>
                    </p>
                    
                    <p>If you have any questions, please contact us at {self.from_email}.</p>
                    <br>
                    <p>Welcome to {self.app_name}!</p>
                    <p><strong>The {self.app_name} Team</strong></p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {self.app_name}. All rights reserved.</p>
                    <p>This email contains sensitive credentials. Please keep it secure.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.client.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_application_rejected(
        self,
        email: str,
        full_name: str,
        course_title: str,
        reason: str
    ) -> bool:
        """
        Send application rejection email.
        
        Args:
            email: Student email
            full_name: Student full name
            course_title: Course title
            reason: Rejection reason
            
        Returns:
            True if sent successfully
        """
        subject = f"Application Update - {self.app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #EF4444; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .reason {{ background: #FEF2F2; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #EF4444; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Application Update</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>Thank you for your interest in <strong>{course_title}</strong>.</p>
                    <p>After careful review, we regret to inform you that your application has not been accepted at this time.</p>
                    
                    <div class="reason">
                        <p><strong>Reason:</strong> {reason}</p>
                    </div>
                    
                    <p>We encourage you to apply for future intakes or explore other courses that may be a better fit.</p>
                    <p>If you have any questions, please contact us at {self.from_email}.</p>
                    <br>
                    <p>Best regards,</p>
                    <p><strong>{self.app_name} Team</strong></p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {self.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.client.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )
    
    # ============================================================
    # GENERAL EMAILS
    # ============================================================
    
    async def send_welcome_email(self, email: str, full_name: str) -> bool:
        """
        Send welcome email to new user.
        
        Args:
            email: User email
            full_name: User full name
            
        Returns:
            True if sent successfully
        """
        subject = f"Welcome to {self.app_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {self.app_name}!</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>We're excited to have you on board!</p>
                    <p>Your account has been created successfully. You can now:</p>
                    <ul>
                        <li>Browse and enroll in courses</li>
                        <li>Access learning materials</li>
                        <li>Join live sessions</li>
                        <li>Track your progress</li>
                    </ul>
                    <p>
                        <a href="{self.app_url}" class="button">Go to Dashboard</a>
                    </p>
                    <p>If you have any questions, feel free to reach out.</p>
                    <br>
                    <p>The {self.app_name} Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {self.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.client.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_password_reset(self, email: str, full_name: str, reset_token: str) -> bool:
        """
        Send password reset email.
        
        Args:
            email: User email
            full_name: User full name
            reset_token: Password reset token
            
        Returns:
            True if sent successfully
        """
        reset_url = f"{self.app_url}/reset-password?token={reset_token}"
        
        subject = f"Password Reset - {self.app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
                .warning {{ color: #DC2626; font-size: 14px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>We received a request to reset your password.</p>
                    <p>Click the button below to set a new password:</p>
                    <p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p class="warning">⚠️ This link will expire in 1 hour.</p>
                    <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
                    <br>
                    <p>The {self.app_name} Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {self.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.client.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )