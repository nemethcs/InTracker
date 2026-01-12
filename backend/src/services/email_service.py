"""Email service using Azure Communication Services Email."""
from typing import Optional, List
from azure.communication.email import EmailClient
from src.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Azure Communication Services Email."""

    def __init__(self):
        """Initialize email client."""
        self.connection_string = settings.AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING
        self.sender_address = settings.AZURE_EMAIL_SENDER_ADDRESS
        self.email_service_name = settings.AZURE_EMAIL_SERVICE_NAME
        
        if not self.connection_string:
            logger.warning("Azure Communication Services connection string not set. Email sending will be disabled.")
            self.client = None
        else:
            try:
                self.client = EmailClient.from_connection_string(self.connection_string)
                logger.info("Azure Communication Services Email client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize email client: {e}")
                self.client = None

    def send_invitation_email(
        self,
        to_email: str,
        invitation_code: str,
        team_name: str,
        inviter_name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> bool:
        """Send team invitation email.
        
        Args:
            to_email: Recipient email address
            invitation_code: Invitation code
            team_name: Name of the team
            inviter_name: Name of the person who sent the invitation
            expires_in_days: Number of days until expiration
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("Email client not initialized. Skipping email send.")
            return False

        # Build invitation URL
        frontend_url = settings.FRONTEND_URL
        if not frontend_url or frontend_url == "*":
            frontend_url = "https://intracker.kesmarki.com"
        invitation_url = f"{frontend_url}/register?code={invitation_code}"
        
        # Build email content
        inviter_text = f" from {inviter_name}" if inviter_name else ""
        expires_text = f" This invitation expires in {expires_in_days} days." if expires_in_days else ""
        
        subject = f"Invitation to join {team_name} on InTracker"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Team Invitation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h1 style="color: #2563eb; margin-top: 0;">You've been invited to join {team_name}!</h1>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                <p>Hello,</p>
                
                <p>You've been invited{inviter_text} to join <strong>{team_name}</strong> on InTracker.{expires_text}</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invitation_url}" 
                       style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Accept Invitation
                    </a>
                </div>
                
                <p style="color: #6b7280; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{invitation_url}" style="color: #2563eb; word-break: break-all;">{invitation_url}</a>
                </p>
                
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                    Your invitation code: <code style="background-color: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{invitation_code}</code>
                </p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; text-align: center;">
                <p>This is an automated message from InTracker. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        plain_text_content = f"""
You've been invited{inviter_text} to join {team_name} on InTracker.{expires_text}

Click here to accept: {invitation_url}

Your invitation code: {invitation_code}

This is an automated message from InTracker. Please do not reply to this email.
        """.strip()

        try:
            message = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": [{"address": to_email}],
                },
                "content": {
                    "subject": subject,
                    "plainText": plain_text_content,
                    "html": html_content,
                },
            }

            poller = self.client.begin_send(message)
            result = poller.result()
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {result.get('messageId')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None,
    ) -> bool:
        """Send a generic email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            plain_text_content: Plain text email content (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("Email client not initialized. Skipping email send.")
            return False

        try:
            message = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": [{"address": to_email}],
                },
                "content": {
                    "subject": subject,
                    "html": html_content,
                    "plainText": plain_text_content or self._html_to_text(html_content),
                },
            }

            poller = self.client.begin_send(message)
            result = poller.result()
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {result.get('messageId')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple implementation)."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities (basic)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# Global email service instance
email_service = EmailService()
