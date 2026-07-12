# ============================================================
# AETHER LINK - EMAIL UTILITY
# ============================================================

import os
import logging
from typing import Optional, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.sendgrid_client = None
        self._init_sendgrid()
    
    def _init_sendgrid(self):
        """Initialize SendGrid client."""
        if settings.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                logger.info("✅ SendGrid client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SendGrid: {e}")
                self.sendgrid_client = None
        else:
            logger.warning("⚠️ SENDGRID_API_KEY not set. Email sending will be disabled.")
    
    def send_invitation_email(
        self,
        to_email: str,
        to_name: str,
        token: str,
        expires_at: str,
        invited_by_name: str = "Admin"
    ) -> bool:
        """
        Send teacher invitation email.
        
        Args:
            to_email: Recipient email
            to_name: Recipient full name
            token: Invitation token
            expires_at: Expiration date
            invited_by_name: Name of inviter
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.error("❌ SendGrid not configured. Email not sent.")
            return False
        
        try:
            # Generate acceptance link
            frontend_url = os.getenv("FRONTEND_URL", "https://aetherlink-frontend.onrender.com")
            accept_link = f"{frontend_url}/accept-invitation?token={token}"
            
            # HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Teacher Invitation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #1a1a2e; color: #f5c518; padding: 30px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .header p {{ margin: 5px 0 0; opacity: 0.8; }}
                    .content {{ padding: 30px 20px; background: #f9f9f9; }}
                    .button {{ 
                        display: inline-block; 
                        padding: 14px 40px; 
                        background: #f5c518; 
                        color: #1a1a2e !important; 
                        text-decoration: none; 
                        border-radius: 8px; 
                        font-weight: bold; 
                        font-size: 16px;
                        margin: 20px 0;
                    }}
                    .button:hover {{ background: #e0b000; }}
                    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; background: #f4f4f4; }}
                    .details {{ background: #fff; border-radius: 8px; padding: 15px; margin: 15px 0; border: 1px solid #e0e0e0; }}
                    .expiry {{ color: #e67e22; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎓 Aether Link</h1>
                        <p>Teacher Invitation</p>
                    </div>
                    <div class="content">
                        <h2>Hello {to_name},</h2>
                        <p>You have been invited to join <strong>Aether Link</strong> as a teacher by <strong>{invited_by_name}</strong>!</p>
                        
                        <div class="details">
                            <p><strong>📧 Email:</strong> {to_email}</p>
                            <p><strong>📅 Expires:</strong> <span class="expiry">{expires_at}</span></p>
                        </div>
                        
                        <p>Click the button below to accept your invitation and set up your account:</p>
                        <p style="text-align: center;">
                            <a href="{accept_link}" class="button">✅ Accept Invitation</a>
                        </p>
                        
                        <p style="font-size: 14px; color: #666;">
                            This invitation link will expire on <strong>{expires_at}</strong>.
                            If you don't accept it by then, you'll need to request a new invitation.
                        </p>
                        <p style="font-size: 14px; color: #666;">
                            If you did not expect this invitation, please ignore this email.
                        </p>
                    </div>
                    <div class="footer">
                        <p>© 2026 Aether Link. All rights reserved.</p>
                        <p>Need help? Contact us at <a href="mailto:{settings.REPLY_TO}">{settings.REPLY_TO}</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            You have been invited to join Aether Link as a teacher!
            
            Invited by: {invited_by_name}
            Email: {to_email}
            Expires: {expires_at}
            
            Accept your invitation here:
            {accept_link}
            
            If you did not expect this invitation, please ignore this email.
            
            Need help? Contact us at: {settings.REPLY_TO}
            
            © 2026 Aether Link
            """
            
            # Create message
            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=to_email,
                subject="🎓 You're Invited to Join Aether Link as a Teacher",
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # ✅ Set reply-to from settings
            if hasattr(settings, 'REPLY_TO') and settings.REPLY_TO:
                message.reply_to = settings.REPLY_TO
                logger.info(f"📧 Reply-To set to: {settings.REPLY_TO}")
            
            # Send email
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Invitation email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ Failed to send email. Status: {response.status_code}")
                logger.error(f"   Response: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Email sending failed: {e}")
            return False


# Singleton instance
email_service = EmailService()


def send_invitation_email(
    to_email: str,
    to_name: str,
    token: str,
    expires_at: str,
    invited_by_name: str = "Admin"
) -> bool:
    """Wrapper function to send invitation email."""
    return email_service.send_invitation_email(
        to_email=to_email,
        to_name=to_name,
        token=token,
        expires_at=expires_at,
        invited_by_name=invited_by_name
    )