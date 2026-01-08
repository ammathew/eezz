#!/usr/bin/env python
"""
Test script to preview new subject line format.
"""
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from api.models import Conversation
from dream_brain.services.reflection_generator import ReflectionGenerator

def test_subject_lines():
    """Show what subject lines look like with different dream ages"""

    # Get a real conversation
    conv = Conversation.objects.first()

    if not conv:
        print("No conversations found!")
        return

    print("=" * 60)
    print("SUBJECT LINE FORMAT PREVIEW")
    print("=" * 60)
    print()

    # Simulate different dream ages
    original_date = conv.created_at
    test_ages = [1, 2, 4, 6, 14]

    for days_ago in test_ages:
        # Temporarily set conversation date
        conv.created_at = timezone.now() - timedelta(days=days_ago)

        # Generate subject
        now = timezone.now()
        dream_date = conv.created_at
        days_diff = (now - dream_date).days

        # Format date as MM/DD
        formatted_date = dream_date.strftime('%m/%d')

        # Handle singular vs plural
        if days_diff == 1:
            days_text = "1 day ago"
        else:
            days_text = f"{days_diff} days ago"

        subject_line = f"Re: Your dream from {days_text} ({formatted_date})"

        print(f"Dream age: {days_ago} days")
        print(f"Subject:   {subject_line}")
        print()

    # Restore original date
    conv.created_at = original_date

if __name__ == '__main__':
    test_subject_lines()
