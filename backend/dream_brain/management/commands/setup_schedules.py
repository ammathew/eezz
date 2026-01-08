# -*- coding: utf-8 -*-
"""
Management command to set up Django Q scheduled tasks.

Usage:
    python manage.py setup_schedules
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'Set up Django Q scheduled tasks for Dream Brain'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"SETUP DJANGO Q SCHEDULES\n"
            f"{'='*60}\n"
        ))

        # Daily Insights Task - runs every day at 3:30 PM EST (8:30 PM UTC)
        # Using cron: "30 20 * * *" = At 8:30 PM UTC (3:30 PM EST)
        schedule, created = Schedule.objects.update_or_create(
            name='send_daily_insights',
            defaults={
                'func': 'dream_brain.tasks.send_daily_insights',
                'schedule_type': Schedule.CRON,
                'cron': '30 20 * * *',  # At 8:30 PM UTC (3:30 PM EST)
                'repeats': -1,  # Repeat indefinitely
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                "✓ Created 'send_daily_insights' schedule (Daily at 3:30 PM EST / 8:30 PM UTC)"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "✓ Updated 'send_daily_insights' schedule (Daily at 3:30 PM EST / 8:30 PM UTC)"
            ))

        # Process Stale Conversations Task - runs every 6 hours
        # Using cron: "0 */6 * * *" = At minute 0 past every 6th hour (00:00, 06:00, 12:00, 18:00 UTC)
        schedule, created = Schedule.objects.update_or_create(
            name='process_stale_conversations',
            defaults={
                'func': 'dream_brain.tasks.process_stale_conversations',
                'schedule_type': Schedule.CRON,
                'cron': '0 */6 * * *',  # Every 6 hours
                'repeats': -1,  # Repeat indefinitely
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                "✓ Created 'process_stale_conversations' schedule (Every 6 hours)"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "✓ Updated 'process_stale_conversations' schedule (Every 6 hours)"
            ))

        # Public User Insights Task - runs daily at 10:00 AM EST (3:00 PM UTC)
        # Using cron: "0 15 * * *" = At 3:00 PM UTC (10:00 AM EST)
        schedule, created = Schedule.objects.update_or_create(
            name='send_public_user_insights',
            defaults={
                'func': 'dream_brain.tasks.send_public_user_insights',
                'schedule_type': Schedule.CRON,
                'cron': '0 15 * * *',  # At 3:00 PM UTC (10:00 AM EST)
                'repeats': -1,  # Repeat indefinitely
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                "✓ Created 'send_public_user_insights' schedule (Daily at 10:00 AM EST / 3:00 PM UTC)"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "✓ Updated 'send_public_user_insights' schedule (Daily at 10:00 AM EST / 3:00 PM UTC)"
            ))

        # Display all schedules
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("ACTIVE SCHEDULES")
        self.stdout.write(f"{'='*60}\n")

        schedules = Schedule.objects.all()
        for sched in schedules:
            self.stdout.write(
                f"Name: {sched.name}\n"
                f"  Function: {sched.func}\n"
                f"  Type: {sched.get_schedule_type_display()}\n"
                f"  Next run: {sched.next_run}\n"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"✓ Schedules configured!\n"
            f"Run 'python manage.py qcluster' to start the task queue\n"
            f"{'='*60}\n"
        ))
