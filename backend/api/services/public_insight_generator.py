"""
Public User Insight Generator Service
Generates follow-up insights for public dream submission users.
"""
from django.utils import timezone
from datetime import timedelta
import logging
import markdown

from api.models import PublicDreamSubmission
from api.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class PublicInsightGenerator:
    """
    Generates follow-up insights for public dream submission users.
    Sends insights every 2 days to encourage signup.
    Consolidates all dreams from the same email for better context.
    """

    def __init__(self):
        self.gemini = GeminiService()

    def find_emails_for_insight(self, force=False):
        """
        Find unique email addresses that should receive a follow-up insight.
        Deduplicates by email address and returns one representative submission per email.

        Args:
            force: If True, ignore timing requirements and return all eligible emails

        Criteria:
        - Has email address
        - Status is 'sent' (initial interpretation was sent)
        - User is subscribed (email_subscribed=True)
        - Either never received a follow-up, OR last one was 2+ days ago (unless force=True)
        - Initial email was sent at least 2 days ago (unless force=True)

        Returns:
            List of dicts with 'email' and 'submissions' (all submissions for that email)
        """
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)

        # Find all submissions that meet base criteria
        # Exclude 'failed' status which includes inactive/bounced emails
        query = PublicDreamSubmission.objects.filter(
            email__isnull=False,
            status='sent',  # Only sent emails (excludes 'failed', 'skipped', etc.)
            email_subscribed=True,
        )

        # Apply timing filter only if not forcing
        if not force:
            query = query.filter(email_sent_at__lte=two_days_ago)

        submissions = query.order_by('email', '-created_at')

        # Group by email and check if any submission from that email is ready
        email_groups = {}
        for submission in submissions:
            if submission.email not in email_groups:
                email_groups[submission.email] = []
            email_groups[submission.email].append(submission)

        # Filter email groups where at least one submission is ready for insight
        emails_ready = []
        for email, group_submissions in email_groups.items():
            # If forcing, skip timing checks
            if force:
                emails_ready.append({
                    'email': email,
                    'submissions': group_submissions
                })
                continue

            # Check if ANY submission from this email is ready for insight
            is_ready = False
            for submission in group_submissions:
                if submission.last_insight_sent_at is None:
                    # Never received a follow-up insight
                    is_ready = True
                    break
                elif submission.last_insight_sent_at <= two_days_ago:
                    # Last insight was 2+ days ago
                    is_ready = True
                    break

            if is_ready:
                emails_ready.append({
                    'email': email,
                    'submissions': group_submissions
                })

        logger.info(f"Found {len(emails_ready)} unique emails ready for follow-up insights (force={force})")
        logger.info(f"Total submissions across all emails: {sum(len(g['submissions']) for g in emails_ready)}")
        return emails_ready

    def generate_insight_content(self, submissions):
        """
        Generate AI-powered follow-up insight for public dream submissions.
        Consolidates all dreams from the same user for better context.

        Args:
            submissions: List of PublicDreamSubmission objects from the same email

        Returns:
            dict: {
                'subject': str,
                'content': str (markdown)
            }
        """
        try:
            # Handle both single submission and list
            if not isinstance(submissions, list):
                submissions = [submissions]

            email = submissions[0].email
            logger.info(f"Generating follow-up insight for {email} ({len(submissions)} dream(s))")

            # Build the prompt for Gemini with all dreams
            prompt = self._build_insight_prompt(submissions)

            # Get AI-generated insight
            response = self.gemini.generate_simple_response(prompt)

            # Parse the response - just use the content, ignore any generated subject
            content = response.strip()

            # Remove subject line if generated
            lines = content.split('\n')
            if lines and (lines[0].startswith('Subject:') or lines[0].startswith('**Subject:**')):
                content = '\n'.join(lines[1:]).strip()

            # Generate date-based subject line
            from django.utils import timezone
            today = timezone.now()
            subject = f"Your dream insights for {today.strftime('%b %-d')}"

            result = {
                'subject': subject,
                'content': content
            }

            logger.info(f"Successfully generated insight for {email}")
            return result

        except Exception as e:
            logger.error(f"Error generating insight for {email}: {str(e)}")
            raise

    def _build_insight_prompt(self, submissions):
        """Build the prompt for generating a follow-up insight with all dreams from the same user"""

        # Handle both single submission and list
        if not isinstance(submissions, list):
            submissions = [submissions]

        # Build dream context - include ALL dreams from this email
        if len(submissions) == 1:
            submission = submissions[0]
            dreams_context = f"DREAM:\n{submission.dream_text}\n\nPREVIOUS INTERPRETATION:\n{submission.interpretation}"
        else:
            dreams_context = f"You previously submitted {len(submissions)} dreams:\n\n"
            for i, sub in enumerate(submissions, 1):
                dreams_context += f"DREAM {i}: {sub.dream_text}\n\nINTERPRETATION {i}: {sub.interpretation}\n\n"

        prompt = f"""You are a dream expert. Provide a follow-up insight for someone who submitted {'a dream' if len(submissions) == 1 else 'multiple dreams'}.

{dreams_context}

{"Identify patterns and themes across their dreams." if len(submissions) > 1 else "Go deeper than the original interpretation."}

IMPORTANT FORMATTING RULES:
- Under 200 words total
- Use bullet points to highlight key insights
- Maximum 3 sentences per paragraph
- Keep it scannable and easy to read
- End with 1-2 reflection questions
- Encourage them to sign up for Unravel to track dreams over time

Use markdown formatting with headers, bullet points, and bold text for emphasis.
"""

        return prompt
