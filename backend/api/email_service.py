from django.conf import settings
from django.utils import timezone
import logging
import markdown
from .ghl_service import GHLService
from emails.services.base import BaseEmailService

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending dream interpretation emails via Postmark"""

    @staticmethod
    def send_dream_interpretation(submission):
        """
        Send dream interpretation email to the user

        Args:
            submission: PublicDreamSubmission instance

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not submission.email:
            logger.error(f"No email provided for submission {submission.submission_id}")
            return False

        if not submission.interpretation:
            logger.error(f"No interpretation available for submission {submission.submission_id}")
            return False

        try:
            logger.info(f"Preparing email for submission {submission.submission_id}")

            # Check if email belongs to an existing app user with at least one conversation
            from django.contrib.auth.models import User
            from api.models import Conversation

            existing_user = User.objects.filter(email=submission.email).first()
            if existing_user:
                has_conversations = Conversation.objects.filter(user=existing_user).exists()
                if has_conversations:
                    logger.info(f"Skipping public interpretation email for {submission.email} - user has app account with conversations")
                    submission.status = 'skipped'
                    submission.save()
                    return False

            # Ensure unsubscribe token exists
            if not submission.unsubscribe_token:
                import uuid
                submission.unsubscribe_token = uuid.uuid4()
                submission.save(update_fields=['unsubscribe_token'])

            # Convert markdown interpretation to HTML
            interpretation_html = markdown.markdown(
                submission.interpretation,
                extensions=['nl2br', 'fenced_code']
            )

            # Build unsubscribe URL
            unsubscribe_url = f"{settings.FRONTEND_URL}/public-unsubscribe/{submission.unsubscribe_token}"

            # Prepare email context
            context = {
                'dream_text': submission.dream_text,
                'interpretation': interpretation_html,
                'submission_id': str(submission.submission_id),  # Convert UUID to string
                'frontend_url': settings.FRONTEND_URL,
                'unsubscribe_url': unsubscribe_url,
            }

            logger.info(f"Sending email to {submission.email} from {settings.DEFAULT_FROM_EMAIL}")

            # Send email using BaseEmailService
            email_service = BaseEmailService()
            email_record = email_service.send(
                user=None,  # Public submission, no user
                recipient_email=submission.email,
                subject='Your Dream Interpretation from Unravel',
                template_name='emails/dream_interpretation.html',
                context=context,
                email_type='public-interpretation',
            )

            if email_record:
                logger.info(f"Email sent successfully via BaseEmailService")

                # Update submission status
                submission.email_sent_at = timezone.now()
                submission.status = 'sent'
                submission.save()

                # Create contact in GoHighLevel
                ghl_result = GHLService.create_contact_from_dream_submission(submission)
                if ghl_result:
                    logger.info(f"GHL contact created for {submission.email}")
                else:
                    logger.warning(f"Failed to create GHL contact for {submission.email}, but email was sent successfully")

                logger.info(f"Dream interpretation email sent to {submission.email} for submission {submission.submission_id}")
                return True
            else:
                logger.error(f"Failed to send email via BaseEmailService for submission {submission.submission_id}")
                submission.status = 'failed'
                submission.save()
                return False

        except Exception as e:
            logger.error(f"Failed to send email for submission {submission.submission_id}: {type(e).__name__}: {str(e)}")
            submission.status = 'failed'
            submission.save()
            return False
