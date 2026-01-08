"""
Base email backend interface.
All email providers should implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseEmailBackend(ABC):
    """
    Abstract base class for email backends.
    Provides a consistent interface for different email providers (Postmark, SendGrid, etc.)
    """

    @abstractmethod
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
        Send an email through the provider.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML version of email body
            text_content: Plain text version of email body
            from_email: Sender email address
            reply_to: Optional reply-to address
            metadata: Optional metadata to attach (for tracking)
            tag: Optional tag for categorizing emails in provider dashboard

        Returns:
            Dict with keys:
                - success: bool
                - message_id: str (provider's message ID)
                - error: Optional[str]
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of this email provider."""
        pass
