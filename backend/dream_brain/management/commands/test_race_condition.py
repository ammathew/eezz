"""
Management command to test the race condition fix for daily insights.
Simulates multiple workers trying to create insights for the same user simultaneously.

Usage:
    python manage.py test_race_condition
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import threading

from dream_brain.services.daily_insight_generator import DailyInsightGenerator
from dream_brain.models import DailyInsight


class Command(BaseCommand):
    help = 'Test race condition fix by simulating multiple workers creating insights simultaneously'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=5,
            help='Number of worker threads to simulate (default: 5)',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of specific user to test (default: first user with conversations)',
        )

    def handle(self, *args, **options):
        num_workers = options['workers']
        user_email = options.get('user_email')

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("TESTING RACE CONDITION FIX"))
        self.stdout.write("=" * 60)

        # Get test user
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with email {user_email} not found"))
                return
        else:
            user = User.objects.filter(conversations__isnull=False).first()

        if not user:
            self.stdout.write(self.style.ERROR("No users with conversations found. Cannot test."))
            return

        self.stdout.write(f"\nTest User: {user.email}")

        # Temporarily set the last insight to 25 hours ago to allow new insight creation
        last_insight = DailyInsight.objects.filter(user=user).order_by('-created_at').first()
        original_created_at = None

        if last_insight:
            original_created_at = last_insight.created_at
            # Set it to 25 hours ago
            last_insight.created_at = timezone.now() - timedelta(hours=25)
            last_insight.save()
            self.stdout.write(f"Temporarily set last insight to 25 hours ago (was: {original_created_at})")

        # Count existing insights
        initial_count = DailyInsight.objects.filter(user=user).count()
        self.stdout.write(f"Initial insights count: {initial_count}")

        # Simulate multiple workers
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Spawning {num_workers} worker threads to create insights simultaneously...")
        self.stdout.write(f"{'='*60}\n")

        results = []
        threads = []

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
                    self.stdout.write(self.style.SUCCESS(f"✓ Worker {worker_id}: Created insight {insight.insight_id}"))
                else:
                    results.append({
                        'worker_id': worker_id,
                        'success': False,
                        'reason': 'Skipped (race condition prevented)'
                    })
                    self.stdout.write(self.style.WARNING(f"✗ Worker {worker_id}: Insight creation skipped (race condition prevented)"))
            except Exception as e:
                results.append({
                    'worker_id': worker_id,
                    'success': False,
                    'error': str(e)
                })
                self.stdout.write(self.style.ERROR(f"✗ Worker {worker_id}: Error - {e}"))

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
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("RESULTS"))
        self.stdout.write(f"{'='*60}")

        final_count = DailyInsight.objects.filter(user=user).count()
        created_count = final_count - initial_count

        successful_creates = sum(1 for r in results if r.get('success'))

        self.stdout.write(f"\nWorkers that succeeded: {successful_creates}/{num_workers}")
        self.stdout.write(f"Insights created: {created_count}")
        self.stdout.write(f"Final insights count: {final_count}")

        # Clean up: Delete the test insights we created
        if created_count > 0:
            test_insights = DailyInsight.objects.filter(
                user=user
            ).order_by('-created_at')[:created_count]

            self.stdout.write(f"\nCleaning up {created_count} test insight(s)...")
            for insight in test_insights:
                self.stdout.write(f"  Deleting: {insight.insight_id}")
                insight.delete()

        # Restore original timestamp
        if last_insight and original_created_at:
            last_insight.refresh_from_db()
            last_insight.created_at = original_created_at
            last_insight.save()
            self.stdout.write(f"Restored original timestamp: {original_created_at}")

        # Final verdict
        self.stdout.write(f"\n{'='*60}")
        if created_count == 1:
            self.stdout.write(self.style.SUCCESS("✓ SUCCESS: Only 1 insight was created (race condition prevented)"))
            self.stdout.write(self.style.SUCCESS("The database lock is working correctly!"))
        elif created_count == 0:
            self.stdout.write(self.style.WARNING("⚠ WARNING: No insights were created"))
            self.stdout.write("This might indicate an issue with the test setup")
        else:
            self.stdout.write(self.style.ERROR(f"✗ FAIL: {created_count} insights were created (race condition NOT prevented)"))
            self.stdout.write(self.style.ERROR("The database lock is NOT working correctly!"))
        self.stdout.write(f"{'='*60}\n")
