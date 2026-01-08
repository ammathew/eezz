"""
Django Q tasks for Dream Brain scheduled operations.
"""
import logging
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from dream_brain.services.daily_insight_generator import DailyInsightGenerator
from dream_brain.services.email_scheduler import filter_users_by_email_preference
from dream_brain.services.timeline_service import TimelineService
from dream_brain.models import TimelineEvent
from api.models import Conversation
from api.services.public_insight_generator import PublicInsightGenerator
from emails.services.base import BaseEmailService
import markdown

logger = logging.getLogger(__name__)


def send_daily_insights():
    """
    Scheduled task to generate and send daily insights.
    Runs daily and respects user email frequency preferences.

    This task:
    1. Finds all users eligible for daily insights
    2. Filters by email frequency preferences
    3. Generates personalized insights
    4. Sends emails

    If DAILY_INSIGHTS_TEST_EMAIL is set, only sends to that specific user (for testing).
    """
    from django.conf import settings

    logger.info("=" * 60)
    logger.info("DREAM BRAIN - DAILY INSIGHTS TASK")
    logger.info("=" * 60)

    try:
        # Initialize services
        generator = DailyInsightGenerator()
        email_service = BaseEmailService()

        # Check for test mode
        test_email = getattr(settings, 'DAILY_INSIGHTS_TEST_EMAIL', '')
        if test_email:
            logger.warning(f"TEST MODE: Only sending to {test_email}")

        # Step 1: Find all eligible users (have dreams, 24+ hours since last insight)
        logger.info("[Step 1] Finding eligible users...")
        all_eligible_users = generator.find_users_for_daily_insight()
        logger.info(f"Found {len(all_eligible_users)} eligible users")

        # Step 2: Filter by email preferences (daily, every 2 days, etc.)
        logger.info("[Step 2] Filtering by email preferences...")
        users_to_email = filter_users_by_email_preference(all_eligible_users)
        logger.info(f"After filtering: {len(users_to_email)} users should receive emails today")

        # Step 2.5: If test mode, filter to only test user
        if test_email:
            users_to_email = [u for u in users_to_email if u.email == test_email]
            logger.warning(f"TEST MODE: Filtered to {len(users_to_email)} user(s) matching {test_email}")

        if not users_to_email:
            logger.info("No users to email today")
            return {
                'status': 'success',
                'eligible_users': len(all_eligible_users),
                'users_to_email': 0,
                'sent': 0,
                'failed': 0
            }

        # Step 3: Generate and send insights
        logger.info("[Step 3] Generating and sending insights...")
        sent_count = 0
        failed_count = 0

        for user in users_to_email:
            try:
                # Generate insight
                daily_insight = generator.create_daily_insight(user)

                if not daily_insight:
                    logger.error(f"Failed to generate insight for {user.email}")
                    failed_count += 1
                    continue

                # Convert markdown to HTML
                content_html = markdown.markdown(
                    daily_insight.content,
                    extensions=['extra']
                )

                # Send email
                email = email_service.send(
                    user=user,
                    recipient_email=user.email,
                    subject=daily_insight.subject,
                    template_name='emails/daily_insight.html',
                    context={
                        'user_name': user.first_name or user.username,
                        'subject': daily_insight.subject,
                        'insight_content': content_html,
                    },
                    email_type='appuser-followup',
                    reply_to=daily_insight.reply_to_email
                )

                if email:
                    # Update insight record
                    daily_insight.email = email
                    daily_insight.status = 'sent'
                    daily_insight.sent_at = timezone.now()
                    daily_insight.save()

                    sent_count += 1
                    logger.info(f"✓ Sent to {user.email}")
                else:
                    daily_insight.status = 'failed'
                    daily_insight.failed_reason = "Email service returned None"
                    daily_insight.save()

                    failed_count += 1
                    logger.error(f"✗ Failed to send to {user.email}")

            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Error for {user.email}: {type(e).__name__}: {str(e)}")

        # Summary
        logger.info("=" * 60)
        logger.info("TASK SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Eligible users: {len(all_eligible_users)}")
        logger.info(f"Users to email today: {len(users_to_email)}")
        logger.info(f"Successfully sent: {sent_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info("=" * 60)

        return {
            'status': 'success',
            'eligible_users': len(all_eligible_users),
            'users_to_email': len(users_to_email),
            'sent': sent_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Task failed: {type(e).__name__}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def process_stale_conversations():
    """
    Scheduled task to process conversations that have gone idle.
    Creates timeline events (dream and chat summary) for conversations
    that haven't had activity in a configurable time period.

    This task:
    1. Finds conversations with no activity in the last 6 hours
    2. Creates dream timeline events if not already created
    3. Creates chat summary timeline events if not already created (and conversation has >1 message)

    Returns summary of processing results.
    """
    logger.info("=" * 60)
    logger.info("DREAM BRAIN - PROCESS STALE CONVERSATIONS TASK")
    logger.info("=" * 60)

    try:
        # Configuration: consider conversations "stale" after 1 hour of inactivity
        STALE_THRESHOLD_HOURS = 1
        stale_cutoff = timezone.now() - timedelta(hours=STALE_THRESHOLD_HOURS)

        logger.info(f"[Config] Stale threshold: {STALE_THRESHOLD_HOURS} hours")
        logger.info(f"[Config] Processing conversations last updated before: {stale_cutoff}")

        # Find stale conversations (updated before cutoff, have at least one message)
        stale_conversations = Conversation.objects.filter(
            updated_at__lt=stale_cutoff,
            messages__isnull=False
        ).distinct().order_by('updated_at')

        total_conversations = stale_conversations.count()
        logger.info(f"Found {total_conversations} stale conversation(s)")

        if total_conversations == 0:
            logger.info("No stale conversations to process")
            return {
                'status': 'success',
                'conversations_found': 0,
                'dream_events_created': 0,
                'chat_summaries_created': 0,
                'errors': 0
            }

        # Counters
        dream_events_created = 0
        chat_summaries_created = 0
        errors = 0

        # Process each stale conversation
        for conversation in stale_conversations:
            user = conversation.user
            if not user:
                logger.warning(f"Skipping conversation {conversation.id} - no user associated")
                continue

            logger.info(f"\n[Conversation {conversation.id}] User: {user.email}, Last updated: {conversation.updated_at}")

            try:
                # 1. Check if dream events exist for this conversation
                existing_dream_events = TimelineEvent.objects.filter(
                    user=user,
                    dream=conversation,
                    kind='dream'
                ).exists()

                if not existing_dream_events:
                    # Create dream events
                    logger.info(f"  Creating dream events...")
                    dream_events = TimelineService.create_dream_events(user, conversation)
                    if dream_events:
                        dream_events_created += len(dream_events)
                        logger.info(f"  ✓ Created {len(dream_events)} dream event(s)")
                    else:
                        logger.warning(f"  ✗ No dream events created (empty result)")
                else:
                    logger.info(f"  Dream events already exist, skipping")

                # 2. Check if chat summary exists for this conversation
                # Only create if conversation has multiple messages (indicates a real conversation)
                message_count = conversation.messages.count()
                if message_count > 1:
                    existing_chat_summary = TimelineEvent.objects.filter(
                        user=user,
                        dream=conversation,
                        kind='chat_summary'
                    ).exists()

                    if not existing_chat_summary:
                        # Create chat summary
                        logger.info(f"  Creating chat summary ({message_count} messages)...")
                        chat_summary = TimelineService.create_chat_summary_event(user, conversation)
                        if chat_summary:
                            chat_summaries_created += 1
                            logger.info(f"  ✓ Created chat summary")
                        else:
                            logger.warning(f"  ✗ No chat summary created (empty result)")
                    else:
                        logger.info(f"  Chat summary already exists, skipping")
                else:
                    logger.info(f"  Skipping chat summary (only {message_count} message)")

            except Exception as e:
                errors += 1
                logger.error(f"  ✗ Error processing conversation {conversation.id}: {type(e).__name__}: {str(e)}")

        # Summary
        logger.info("=" * 60)
        logger.info("TASK SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Stale conversations found: {total_conversations}")
        logger.info(f"Dream events created: {dream_events_created}")
        logger.info(f"Chat summaries created: {chat_summaries_created}")
        logger.info(f"Errors: {errors}")
        logger.info("=" * 60)

        return {
            'status': 'success',
            'conversations_found': total_conversations,
            'dream_events_created': dream_events_created,
            'chat_summaries_created': chat_summaries_created,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Task failed: {type(e).__name__}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def send_public_user_insights():
    """
    Scheduled task to generate and send follow-up insights to public dream submission users.
    Runs daily and sends to users who received their last email 2+ days ago.

    This task:
    1. Finds all public submissions eligible for follow-up insights
    2. Generates personalized insights based on their submitted dream
    3. Sends emails with signup CTA
    4. Updates last_insight_sent_at timestamp
    """
    from django.conf import settings

    logger.info("=" * 60)
    logger.info("PUBLIC USER - FOLLOW-UP INSIGHTS TASK")
    logger.info("=" * 60)

    try:
        # Initialize services
        generator = PublicInsightGenerator()
        email_service = BaseEmailService()

        # Step 1: Find all eligible emails (deduplicated)
        logger.info("[Step 1] Finding eligible public users (deduped by email)...")
        emails_to_send = generator.find_emails_for_insight()
        logger.info(f"Found {len(emails_to_send)} unique emails to send to")

        if not emails_to_send:
            logger.info("No public users to email today")
            return {
                'status': 'success',
                'emails_sent': 0,
                'sent': 0,
                'failed': 0
            }

        # Step 2: Generate and send insights
        logger.info("[Step 2] Generating and sending insights...")
        sent_count = 0
        failed_count = 0
        total_emails = len(emails_to_send)

        for idx, email_group in enumerate(emails_to_send, 1):
            email = email_group['email']
            submissions = email_group['submissions']

            try:
                logger.info(f"[{idx}/{total_emails}] Processing {email} ({len(submissions)} dream(s))")

                # Generate insight with ALL dreams from this email
                insight_data = generator.generate_insight_content(submissions)

                if not insight_data:
                    logger.error(f"Failed to generate insight for {email}")
                    failed_count += 1
                    continue

                # Convert markdown to HTML
                content_html = markdown.markdown(
                    insight_data['content'],
                    extensions=['extra']
                )

                # Use first submission's unsubscribe token (all from same email)
                first_submission = submissions[0]
                signup_url = f"{settings.FRONTEND_URL}/signup?email={email}"
                unsubscribe_url = f"{settings.FRONTEND_URL}/public-unsubscribe/{first_submission.unsubscribe_token}"

                # Send email
                email_sent = email_service.send(
                    user=None,  # No user account
                    recipient_email=email,
                    subject=insight_data['subject'],
                    template_name='emails/public_user_insight.html',
                    context={
                        'subject': insight_data['subject'],
                        'insight_content': content_html,
                        'signup_url': signup_url,
                        'unsubscribe_url': unsubscribe_url,
                    },
                    email_type='public-followup',
                )

                if email_sent:
                    # Update ALL submissions from this email
                    now = timezone.now()
                    for sub in submissions:
                        sub.last_insight_sent_at = now
                        sub.save(update_fields=['last_insight_sent_at'])

                    sent_count += 1
                    logger.info(f"✓ [{idx}/{total_emails}] Sent to {email}")
                else:
                    # Email failed - unsubscribe all submissions to prevent retries
                    # This handles bounces, inactive recipients, etc.
                    for sub in submissions:
                        sub.email_subscribed = False
                        sub.save(update_fields=['email_subscribed'])

                    failed_count += 1
                    logger.error(f"✗ [{idx}/{total_emails}] Failed to send to {email} - unsubscribed to prevent retries")

            except Exception as e:
                failed_count += 1
                logger.error(f"✗ [{idx}/{total_emails}] Error for {email}: {type(e).__name__}: {str(e)}")

        # Summary
        logger.info("=" * 60)
        logger.info("TASK SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Unique emails found: {len(emails_to_send)}")
        logger.info(f"Successfully sent: {sent_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info("=" * 60)

        return {
            'status': 'success',
            'emails_sent': len(emails_to_send),
            'sent': sent_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Task failed: {type(e).__name__}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
