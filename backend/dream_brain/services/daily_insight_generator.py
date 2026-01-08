"""
Daily Insight Generator Service
Generates personalized daily emails based on user's entire Dream Brain.
Uses timeline events instead of full chat logs for efficiency.
"""
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import logging
import uuid

from api.models import Conversation
from api.gemini_service import GeminiService
from ..models import DailyInsight
from .timeline_service import TimelineService

logger = logging.getLogger(__name__)


class DailyInsightGenerator:
    """
    Generates daily personalized insights based on user's complete Dream Brain timeline.
    Each day, analyzes timeline events to create new insights.
    """

    def __init__(self):
        self.gemini = GeminiService()

    def find_users_for_daily_insight(self):
        """
        Find users who should receive a daily insight email.

        NOTE: This method finds ALL eligible users. Email frequency filtering
        should be done at the task scheduler level (cron/celery/etc).

        Criteria:
        - Has at least one dream
        - Either never received a daily insight, OR last one was 20+ hours ago

        Returns:
            List of User objects
        """
        from django.db.models import Count, Max

        now = timezone.now()
        yesterday = now - timedelta(hours=20)

        users_ready = []

        # Get all users with at least one dream
        users_with_dreams = User.objects.filter(
            conversations__messages__isnull=False
        ).annotate(
            dream_count=Count('conversations', distinct=True)
        ).filter(
            dream_count__gte=1
        ).distinct()

        for user in users_with_dreams:
            # Check when they last received a daily insight
            last_insight = DailyInsight.objects.filter(user=user).order_by('-created_at').first()

            if not last_insight:
                # Never received one - send first daily insight
                users_ready.append(user)
            elif last_insight.created_at <= yesterday:
                # Last insight was 20+ hours ago - send new one
                users_ready.append(user)

        logger.info(f"Found {len(users_ready)} users ready for daily insights")
        return users_ready

    def generate_daily_insight_content(self, user):
        """
        Generate AI-powered daily insight for a user based on their complete Dream Brain.
        Uses timeline events instead of full chat logs.

        Args:
            user: User object

        Returns:
            Dict with 'subject' and 'content' keys, or None if failed
        """
        try:
            # Use timeline to get condensed dream summary (not full chat logs)
            dreams_summary = TimelineService.get_recent_dreams_summary(user, limit=10)

            # Get the full timeline for broader context
            full_timeline = TimelineService.get_user_timeline(user, limit=20)

            # Timeline contains all context we need (no need for separate Dream Brain context)
            dream_brain_context = None

            # Get today's date for subject
            from django.utils.dateformat import DateFormat
            today = DateFormat(timezone.now())
            formatted_date = today.format('F j')  # e.g., "January 2"

            subject_line = f"Your dream insights for {formatted_date}"

            # Create AI prompt
            prompt = self._create_daily_insight_prompt(
                user,
                dreams_summary,
                full_timeline,
                dream_brain_context
            )

            # Log the complete prompt being sent to LLM
            logger.info("=" * 80)
            logger.info("DAILY INSIGHT PROMPT - SENDING TO LLM")
            logger.info("=" * 80)
            logger.info(f"User: {user.email} (ID: {user.id})")
            logger.info("-" * 80)
            logger.info("FULL PROMPT:")
            logger.info(prompt)
            logger.info("=" * 80)

            # Generate insight using Gemini
            messages = [{'role': 'user', 'content': prompt}]
            insight_content = self.gemini.generate_response(messages)

            if not insight_content:
                logger.error(f"Failed to generate daily insight for user {user.id}")
                return None

            return {
                'subject': subject_line,
                'content': insight_content
            }

        except Exception as e:
            logger.error(f"Error generating daily insight: {type(e).__name__}: {str(e)}")
            return None

    def _create_daily_insight_prompt(self, user, dreams_summary, full_timeline, dream_brain_context):
        """Create the AI prompt for generating daily insight using timeline events."""

        user_name = user.first_name or user.username or "there"

        prompt = f"""You are creating a personalized daily Dream Brain insight email for a user.

This analyzes their ENTIRE dream journey using a distilled timeline of events, not full chat logs.

User's name: {user_name}

{dreams_summary}

{full_timeline}
"""

        # Add Dream Brain context if available
        if dream_brain_context:
            prompt += f"""

THEIR COMPLETE DREAM BRAIN KNOWLEDGE BASE:
(Patterns, insights, and what {user_name} has shared in their own words when replying to previous emails)
{dream_brain_context}

The above represents everything we've learned about {user_name}'s unique subconscious over time.
"""
        else:
            prompt += f"""

This user is just starting their Dream Brain journey - they haven't built their knowledge base yet.
"""

        prompt += f"""

TASK:

Write a daily insight email that:

1. **Suggests a possible meaningful pattern or theme** across their dream journey (use tentative language like "might", "could", "seems to suggest", "may reflect")
2. **References what the user has shared** in their own words to back up the possible pattern
3. **Asks a reflective question** that invites them to reply, confirm, or add their perspective
4. **Uses direct, professional tone** - avoid first person ("I", "we")

Guidelines:
- Look at the TIMELINE to see the story arc of their dreams and responses
- If they have Dream Brain context, reference what they've said previously
- Show possible connections between their dreams and what they've shared about their life
- If they're new, identify possible patterns in their dreams and invite them to share their thoughts
- Keep it conversational but informative
- Use tentative, curious language rather than authoritative statements
- Frame insights as observations and suggestions, not definitive conclusions
- Use the timeline summaries, not full chat transcripts

Formatting:
- Use markdown for emphasis (**bold**)
- Use bullet points with "*" or "-" for lists
- IMPORTANT: Add a blank line before any bullet list (required for proper rendering)
- No paragraph should be more than 3 sentences long
- Short (2-3 paragraphs max)
- Focused on ONE key insight from the timeline
- Direct and simple (5th grade reading level)
- Encouraging them to reply and add to their Dream Brain

Example format:
Here's an opening paragraph.

Here's some context that leads to a list:

* First bullet point
* Second bullet point
* Third bullet point

Closing paragraph with question.

Write ONLY the email body content in plain text with markdown formatting (no subject line).
"""

        return prompt

    def create_daily_insight(self, user):
        """
        Create a DailyInsight record for a user.
        Uses atomic transaction to prevent race conditions when multiple workers
        try to create insights for the same user simultaneously.

        Args:
            user: User object

        Returns:
            DailyInsight object if successful, None otherwise
        """
        from django.db import transaction

        try:
            # Use atomic transaction with select_for_update to prevent race conditions
            # Lock the USER row first to ensure only one worker can create insights for this user
            with transaction.atomic():
                # Lock the user row - this blocks other workers from processing this user
                locked_user = User.objects.select_for_update().get(pk=user.pk)

                # Check again if user should receive an insight (race condition check)
                now = timezone.now()
                yesterday = now - timedelta(hours=20)

                last_insight = DailyInsight.objects.filter(
                    user=locked_user
                ).order_by('-created_at').first()

                # Double-check: if an insight was created in the last 20 hours, skip
                if last_insight and last_insight.created_at > yesterday:
                    logger.warning(
                        f"Skipping user {user.email} - insight already created at {last_insight.created_at} "
                        f"(likely race condition prevented)"
                    )
                    return None

                # Generate content
                insight_data = self.generate_daily_insight_content(user)

                if not insight_data:
                    return None

                # Create unique reply-to email
                insight_id = str(uuid.uuid4())
                postmark_hash = "bc32cb0009d9620534bb064784659bff"
                reply_to_email = f"{postmark_hash}+daily-{insight_id}@inbound.postmarkapp.com"

                # Create DailyInsight record
                daily_insight = DailyInsight.objects.create(
                    user=user,
                    subject=insight_data['subject'],
                    content=insight_data['content'],
                    reply_to_email=reply_to_email,
                    status='pending'
                )

                logger.info(f"Created DailyInsight ({daily_insight.insight_id}) for user {user.id}")
                return daily_insight

        except Exception as e:
            logger.error(f"Error creating daily insight: {type(e).__name__}: {str(e)}")
            return None

    def generate_daily_insights_batch(self, limit=50):
        """
        Generate daily insights for users.

        Args:
            limit: Maximum number of insights to generate

        Returns:
            List of created DailyInsight objects
        """
        users_ready = self.find_users_for_daily_insight()[:limit]
        insights = []

        for user in users_ready:
            daily_insight = self.create_daily_insight(user)
            if daily_insight:
                insights.append(daily_insight)

        logger.info(f"Generated {len(insights)} daily insights")
        return insights
