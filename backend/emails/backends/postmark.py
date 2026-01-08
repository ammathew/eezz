"""
Postmark email backend implementation.
"""
from django.core.mail import send_mail
from django.conf import settings
import logging
from typing import Dict, Optional

try:
    # Use Postmark's custom email class to support tags
    from postmark.django_backend import PMEmailMultiAlternatives as EmailMultiAlternatives
except ImportError:
    # Fallback to standard Django if postmark not installed
    from django.core.mail import EmailMultiAlternatives

from .base import BaseEmailBackend

logger = logging.getLogger(__name__)


class PostmarkBackend(BaseEmailBackend):
    """
    Email backend for Postmark.
    Uses Django's built-in SMTP backend configured for Postmark.
    """

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        from_email: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tag: Optional[str] = None,
    ) -> Dict:
        """
        Send email via Postmark using Django's SMTP backend.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body
            from_email: Sender email
            reply_to: Optional reply-to address
            metadata: Optional metadata (currently not used, but could add as headers)
            tag: Optional tag for categorizing emails in Postmark dashboard

        Returns:
            Dict with success status and message_id or error
        """
        try:
            logger.info(f"Sending email via Postmark to {to_email}: {subject}")
            if reply_to:
                logger.info(f"Reply-To: {reply_to}")
            if tag:
                logger.info(f"Tag: {tag}")

            # Build kwargs for PMEmailMultiAlternatives
            # python-postmark accepts tag and track_opens as constructor kwargs
            email_kwargs = {
                'subject': subject,
                'body': text_content,
                'from_email': from_email,
                'to': [to_email],
                'reply_to': [reply_to] if reply_to else None,
            }

            # Add Postmark-specific parameters if available
            if tag:
                email_kwargs['tag'] = tag

            # Create email using PMEmailMultiAlternatives which supports tag parameter
            email = EmailMultiAlternatives(**email_kwargs)

            # Attach HTML alternative
            email.attach_alternative(html_content, "text/html")

            # Send the email
            result = email.send(fail_silently=False)

            if result == 1:
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    'success': True,
                    'message_id': None,  # Django doesn't return message ID
                    'error': None,
                }
            else:
                logger.error(f"Failed to send email to {to_email}")
                return {
                    'success': False,
                    'message_id': None,
                    'error': 'Email send returned 0 (not sent)',
                }

        except Exception as e:
            logger.error(f"Exception sending email to {to_email}: {type(e).__name__}: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': f"{type(e).__name__}: {str(e)}",
            }

    def get_provider_name(self) -> str:
        """Return provider name."""
        return 'postmark'
