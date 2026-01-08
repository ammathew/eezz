"""
Base email service for sending and tracking emails.
"""
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
import logging
from typing import Optional, Dict, Any

from ..models import Email
from ..backends.postmark import PostmarkBackend

logger = logging.getLogger(__name__)


class BaseEmailService:
    """
    Core email service that all other email services inherit from.
    Handles template rendering, sending, and tracking.
    """

    def __init__(self, backend_name='postmark'):
        """
        Initialize the email service with a specific backend.

        Args:
            backend_name: Name of the email backend to use ('postmark', etc.)
        """
        self.backend = self._get_backend(backend_name)
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@unravel.so')

    def _get_backend(self, backend_name: str):
        """Get the appropriate email backend."""
        if backend_name == 'postmark':
            return PostmarkBackend()
        else:
            raise ValueError(f"Unknown email backend: {backend_name}")

    def send(
        self,
        user: Optional[User],
        recipient_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        email_type: str = 'transactional',
        reply_to: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> Optional[Email]:
        """
        Send an email and track it in the database.

        Args:
            user: Django User object (if recipient is a registered user)
            recipient_email: Recipient's email address
            subject: Email subject line
            template_name: Name of the Django template to render
            context: Context dict for template rendering
            email_type: Type of email ('transactional', 'reflection', etc.)
            reply_to: Optional reply-to address
            from_email: Optional custom from address

        Returns:
            Email object if successful, None if failed
        """
        try:
            # Set defaults
            if not from_email:
                from_email = self.default_from_email

            # Add settings to context
            context['frontend_url'] = getattr(settings, 'FRONTEND_URL', 'https://app.eezz.ad')
            context['support_email'] = getattr(settings, 'SUPPORT_EMAIL', 'support@unravel.so')

            # Render email templates
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)

            # Create Email record
            email = Email.objects.create(
                user=user,
                recipient_email=recipient_email,
                subject=subject,
                template_name=template_name,
                context_data=context,
                email_type=email_type,
                reply_to_email=reply_to,
                from_email=from_email,
                provider_name=self.backend.get_provider_name(),
                status='pending',
            )

            logger.info(f"Created Email record {email.email_id} for {recipient_email}")

            # Send via backend
            result = self.backend.send_email(
                to_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                reply_to=reply_to,
                metadata={'email_id': str(email.email_id)},
                tag=email_type,  # Pass email_type as Postmark tag
            )

            # Update email record based on result
            if result['success']:
                email.status = 'sent'
                email.sent_at = timezone.now()
                email.provider_message_id = result.get('message_id')
                email.save()
                logger.info(f"Email {email.email_id} sent successfully to {recipient_email}")
                return email
            else:
                email.status = 'failed'
                email.save()
                logger.error(f"Email {email.email_id} failed to send: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Exception in send(): {type(e).__name__}: {str(e)}")
            return None

    def get_user_emails(self, user: User, email_type: Optional[str] = None):
        """
        Get all emails sent to a user.

        Args:
            user: Django User object
            email_type: Optional filter by email type

        Returns:
            QuerySet of Email objects
        """
        queryset = Email.objects.filter(user=user)
        if email_type:
            queryset = queryset.filter(email_type=email_type)
        return queryset
