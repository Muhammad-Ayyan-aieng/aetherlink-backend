# ============================================================
# AETHER LINK - EMAIL CLIENT
# ============================================================

import logging
from typing import Optional, List, Dict, Any
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailClient:
    """Email client for sending emails."""
    
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER
        self.from_email = settings.EMAIL_FROM
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email using configured provider.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)
            from_email: Sender email (defaults to settings.EMAIL_FROM)
            
        Returns:
            True if sent successfully, False otherwise
        """
        from_email = from_email or self.from_email
        
        if self.provider == "sendgrid":
            return await self._send_sendgrid(to_email, subject, html_content, text_content, from_email)
        elif self.provider == "resend":
            return await self._send_resend(to_email, subject, html_content, text_content, from_email)
        else:
            logger.warning(f"Unknown email provider: {self.provider}")
            return False
    
    async def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: str
    ) -> bool:
        """Send email using SendGrid."""
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API key not configured")
            return False
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            from_email_obj = Email(from_email)
            to_email_obj = To(to_email)
            
            # Create plain text version if not provided
            if not text_content:
                import re
                text_content = re.sub(r'<[^>]+>', '', html_content)
            
            content = Content("text/html", html_content)
            plain_content = Content("text/plain", text_content)
            
            mail = Mail(from_email_obj, to_email_obj, subject, plain_content)
            mail.add_content(content)
            
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ SendGrid error: {response.status_code} - {response.body}")
                return False
                
        except ImportError:
            logger.warning("SendGrid package not installed. Run: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    async def _send_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: str
    ) -> bool:
        """Send email using Resend."""
        try:
            import resend
            
            resend.api_key = settings.RESEND_API_KEY
            
            params = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            response = resend.Emails.send(params)
            
            logger.info(f"✅ Email sent to {to_email}")
            return True
            
        except ImportError:
            logger.warning("Resend package not installed. Run: pip install resend")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False


# Singleton instance
_email_client: Optional[EmailClient] = None


def get_email_client() -> EmailClient:
    """Get or create email client instance."""
    global _email_client
    if _email_client is None:
        _email_client = EmailClient()
    return _email_client