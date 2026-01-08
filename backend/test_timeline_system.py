#!/usr/bin/env python
"""
Test script for the timeline-based Dream Brain system.

This script tests:
1. Creating timeline events manually
2. Querying timeline data
3. Generating daily insights using timeline
4. Backfilling existing dreams

Usage:
    python test_timeline_system.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Conversation, Message
from dream_brain.models import TimelineEvent, DailyInsight
from dream_brain.services.timeline_service import TimelineService
from dream_brain.services.daily_insight_generator import DailyInsightGenerator


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Print a section divider"""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80)


def test_timeline_creation():
    """Test creating timeline events"""
    print_header("TEST 1: Timeline Event Creation")

    # Get or create test user
    user, created = User.objects.get_or_create(
        username='timeline_test_user',
        defaults={'email': 'timeline_test@example.com'}
    )
    if created:
        print(f"✓ Created test user: {user.email}")
    else:
        print(f"✓ Using existing test user: {user.email}")

    # Create a test dream conversation
    conversation = Conversation.objects.create(
        user=user,
        title="Test Dream - Flying Over City"
    )
    print(f"✓ Created test conversation: {conversation.id}")

    # Add dream message
    dream_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content="I was flying over a beautiful city at sunset. The buildings were golden and I felt free."
    )
    print(f"✓ Added dream message")

    # Create dream timeline event
    dream_event = TimelineService.create_dream_event(user, conversation)
    if dream_event:
        print(f"✓ Created dream event: {dream_event.event_id}")
        print(f"  - Kind: {dream_event.kind}")
        print(f"  - Data: {dream_event.data}")
    else:
        print(f"✗ Failed to create dream event")
        return False

    # Add AI response
    ai_message = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content="Flying dreams often represent freedom and empowerment. The golden city suggests positive transformation."
    )
    print(f"✓ Added AI interpretation message")

    # Create chat summary event
    summary_event = TimelineService.create_chat_summary_event(user, conversation)
    if summary_event:
        print(f"✓ Created chat summary event: {summary_event.event_id}")
        print(f"  - Summary: {summary_event.data.get('summary', 'N/A')}")
        print(f"  - Themes: {summary_event.data.get('key_themes', [])}")
    else:
        print(f"✗ Failed to create chat summary event")

    return True


def test_timeline_query():
    """Test querying timeline data"""
    print_header("TEST 2: Timeline Querying")

    user = User.objects.filter(username='timeline_test_user').first()
    if not user:
        print("✗ Test user not found. Run test 1 first.")
        return False

    # Get user timeline
    timeline_text = TimelineService.get_user_timeline(user, limit=10)
    print(f"✓ Retrieved timeline for {user.email}:")
    print("\n" + timeline_text)

    # Get recent dreams summary
    dreams_summary = TimelineService.get_recent_dreams_summary(user, limit=5)
    print(f"\n✓ Retrieved dreams summary:")
    print("\n" + dreams_summary)

    # Count timeline events
    event_count = TimelineEvent.objects.filter(user=user).count()
    print(f"\n✓ Total timeline events: {event_count}")

    return True


def test_daily_insight_with_timeline():
    """Test generating daily insight using timeline"""
    print_header("TEST 3: Daily Insight Generation with Timeline")

    user = User.objects.filter(username='timeline_test_user').first()
    if not user:
        print("✗ Test user not found. Run test 1 first.")
        return False

    # Check if user has timeline events
    event_count = TimelineEvent.objects.filter(user=user).count()
    if event_count == 0:
        print("✗ No timeline events found. Run test 1 first.")
        return False

    print(f"✓ User has {event_count} timeline events")

    # Generate daily insight
    print("\nGenerating daily insight...")
    generator = DailyInsightGenerator()

    try:
        insight_data = generator.generate_daily_insight_content(user)

        if insight_data:
            print(f"✓ Generated daily insight:")
            print(f"\n  Subject: {insight_data['subject']}")
            print(f"\n  Content:\n{insight_data['content']}")
            return True
        else:
            print("✗ Failed to generate daily insight")
            return False

    except Exception as e:
        print(f"✗ Error generating insight: {e}")
        return False


def test_email_response_summary():
    """Test creating email response summary event"""
    print_header("TEST 4: Email Response Summary Event")

    user = User.objects.filter(username='timeline_test_user').first()
    if not user:
        print("✗ Test user not found. Run test 1 first.")
        return False

    # Get the test conversation
    conversation = user.conversations.first()
    if not conversation:
        print("✗ No conversation found. Run test 1 first.")
        return False

    # Simulate email response
    response_content = """
    This really resonates with me! I've been feeling more empowered at work lately
    after getting a promotion. The golden city might represent my career growth.
    """

    # Create email response summary event
    response_event = TimelineService.create_email_response_summary_event(
        user=user,
        response_content=response_content,
        dream=conversation,
        source_type='daily_insight'
    )

    if response_event:
        print(f"✓ Created email response summary event: {response_event.event_id}")
        print(f"  - Summary: {response_event.data.get('summary', 'N/A')}")
        print(f"  - Emotional tone: {response_event.data.get('emotional_tone', 'N/A')}")
        print(f"  - Key points: {response_event.data.get('key_points', [])}")
        return True
    else:
        print(f"✗ Failed to create email response summary event")
        return False


def test_timeline_stats():
    """Show timeline statistics"""
    print_header("TIMELINE STATISTICS")

    # Overall stats
    total_events = TimelineEvent.objects.count()
    total_users = TimelineEvent.objects.values('user').distinct().count()

    print(f"Total timeline events: {total_events}")
    print(f"Users with timeline events: {total_users}")

    # Events by kind
    print("\nEvents by kind:")
    for kind, label in TimelineEvent.EVENT_KIND_CHOICES:
        count = TimelineEvent.objects.filter(kind=kind).count()
        print(f"  {label}: {count}")

    # Recent events
    print("\nMost recent 5 events:")
    recent_events = TimelineEvent.objects.order_by('-at')[:5]
    for event in recent_events:
        print(f"  - [{event.at.strftime('%Y-%m-%d %H:%M')}] {event.get_kind_display()} for {event.user.email}")


def cleanup_test_data():
    """Clean up test data"""
    print_header("CLEANUP")

    user = User.objects.filter(username='timeline_test_user').first()
    if user:
        # Delete timeline events
        event_count = TimelineEvent.objects.filter(user=user).count()
        TimelineEvent.objects.filter(user=user).delete()
        print(f"✓ Deleted {event_count} timeline events")

        # Delete conversations and messages
        conversation_count = Conversation.objects.filter(user=user).count()
        Conversation.objects.filter(user=user).delete()
        print(f"✓ Deleted {conversation_count} conversations")

        # Delete daily insights
        insight_count = DailyInsight.objects.filter(user=user).count()
        DailyInsight.objects.filter(user=user).delete()
        print(f"✓ Deleted {insight_count} daily insights")

        # Delete user
        user.delete()
        print(f"✓ Deleted test user")
    else:
        print("No test user found to clean up")


def main():
    """Run all tests"""
    print_header("TIMELINE SYSTEM TEST SUITE")
    print("Testing the timeline-based Dream Brain architecture")

    try:
        # Run tests
        tests = [
            ("Timeline Event Creation", test_timeline_creation),
            ("Timeline Querying", test_timeline_query),
            ("Email Response Summary", test_email_response_summary),
            ("Daily Insight with Timeline", test_daily_insight_with_timeline),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n✗ Test failed with exception: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))

        # Show statistics
        test_timeline_stats()

        # Show results
        print_header("TEST RESULTS")
        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{status}: {test_name}")

        print(f"\n{passed}/{total} tests passed")

        # Ask about cleanup
        print_section("Cleanup")
        try:
            response = input("Do you want to clean up test data? (y/n): ")
            if response.lower() == 'y':
                cleanup_test_data()
            else:
                print("Test data retained. Run cleanup manually if needed.")
        except EOFError:
            # Non-interactive mode or EOF
            print("Skipping cleanup (non-interactive mode)")
            print("Test data retained. Run 'python test_timeline_system.py' with cleanup if needed.")

        return passed == total

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
