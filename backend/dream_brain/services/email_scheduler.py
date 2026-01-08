"""
Email Scheduler Utilities

Helper functions for task schedulers (Celery, cron, etc.) to determine
which users should receive emails based on their preferences.

Usage in your task scheduler:
    from dream_brain.services.email_scheduler import should_send_email_today

    if should_send_email_today(user):
        # Generate and send email
        ...
"""
from django.utils import timezone
from datetime import timedelta
from dream_brain.models import DailyInsight


def should_send_email_today(user):
    """
    Check if a user should receive a daily insight email today based on their preferences.

    Args:
        user: User object

    Returns:
        bool: True if email should be sent, False otherwise
    """
    try:
        profile = user.profile
    except:
        # No profile, don't send
        return False

    # Check if emails are turned off
    if profile.email_frequency == 'off':
        return False

    # Get the time threshold based on frequency
    frequency_days = {
        'daily': 1,
        'every_2_days': 2,
        'every_3_days': 3,
        'every_5_days': 5,
        'weekly': 7,
    }

    days_between = frequency_days.get(profile.email_frequency, 1)
    now = timezone.now()
    threshold = now - timedelta(days=days_between)

    # Check when they last received a daily insight
    last_insight = DailyInsight.objects.filter(user=user).order_by('-created_at').first()

    if not last_insight:
        # Never received one - send it
        return True

    # Send if last insight was >= frequency setting ago
    return last_insight.created_at <= threshold


def filter_users_by_email_preference(users):
    """
    Filter a list of users to only those who should receive emails today.

    Args:
        users: List or QuerySet of User objects

    Returns:
        List of User objects who should receive emails
    """
    return [user for user in users if should_send_email_today(user)]


# Example usage in a Celery task or cron job:
"""
from dream_brain.services.daily_insight_generator import DailyInsightGenerator
from dream_brain.services.email_scheduler import filter_users_by_email_preference

# Get all eligible users
generator = DailyInsightGenerator()
all_users = generator.find_users_for_daily_insight()

# Filter by email preferences
users_to_email = filter_users_by_email_preference(all_users)

# Generate and send emails
for user in users_to_email:
    insight = generator.create_daily_insight(user)
    # ... send email ...
"""
