#!/usr/bin/env python
"""
Test script to verify the race condition fix for daily insights.
Simulates multiple workers trying to create insights for the same user simultaneously.
"""
import os
import django
import threading
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from dream_brain.services.daily_insight_generator import DailyInsightGenerator
from dream_brain.models import DailyInsight
from django.utils import timezone


def create_insight_worker(user, worker_id, results):
    """Worker thread that tries to create a daily insight."""
    try:
        generator = DailyInsightGenerator()
        insight = generator.create_daily_insight(user)

        if insight:
            results.append({
                'worker_id': worker_id,
                'success': True,
                'insight_id': str(insight.insight_id)
            })
            print(f"✓ Worker {worker_id}: Created insight {insight.insight_id}")
        else:
            results.append({
                'worker_id': worker_id,
                'success': False,
                'reason': 'create_daily_insight returned None (race condition prevented)'
            })
            print(f"✗ Worker {worker_id}: Insight creation skipped (expected if race condition)")
    except Exception as e:
        results.append({
            'worker_id': worker_id,
            'success': False,
            'error': str(e)
        })
        print(f"✗ Worker {worker_id}: Error - {e}")


def test_race_condition():
    """Test that only one insight is created when multiple workers run simultaneously."""
    print("=" * 60)
    print("TESTING RACE CONDITION FIX")
    print("=" * 60)

    # Get a test user (use first user with dreams)
    user = User.objects.filter(conversations__isnull=False).first()

    if not user:
        print("No users with conversations found. Cannot test.")
        return

    print(f"\nTest User: {user.email}")

    # Count existing insights
    initial_count = DailyInsight.objects.filter(user=user).count()
    print(f"Initial insights count: {initial_count}")

    # Simulate 5 workers trying to create insights simultaneously
    print(f"\n{'='*60}")
    print("Spawning 5 worker threads to create insights simultaneously...")
    print(f"{'='*60}\n")

    results = []
    threads = []
    num_workers = 5

    # Start all threads at roughly the same time
    for i in range(num_workers):
        thread = threading.Thread(
            target=create_insight_worker,
            args=(user, i+1, results)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")

    final_count = DailyInsight.objects.filter(user=user).count()
    created_count = final_count - initial_count

    successful_creates = sum(1 for r in results if r.get('success'))

    print(f"\nWorkers that succeeded: {successful_creates}/{num_workers}")
    print(f"Insights created: {created_count}")
    print(f"Final insights count: {final_count}")

    if created_count == 1:
        print("\n✓ SUCCESS: Only 1 insight was created (race condition prevented)")
        return True
    elif created_count == 0:
        print("\n⚠ WARNING: No insights were created (may need to check last_insight timing)")
        return False
    else:
        print(f"\n✗ FAIL: {created_count} insights were created (race condition NOT prevented)")

        # Show the duplicate insights
        recent_insights = DailyInsight.objects.filter(
            user=user
        ).order_by('-created_at')[:created_count]

        print("\nDuplicate insights created:")
        for insight in recent_insights:
            print(f"  - {insight.insight_id} at {insight.created_at}")

        return False


if __name__ == '__main__':
    test_race_condition()
