# -*- coding: utf-8 -*-
"""
Management command to delete all dream timeline events.

This is useful when you need to regenerate dream events with updated logic.
Chat summaries and email responses will be preserved.

Usage:
    python manage.py delete_dream_events
    python manage.py delete_dream_events --dry-run
"""
from django.core.management.base import BaseCommand
from dream_brain.models import TimelineEvent


class Command(BaseCommand):
    help = 'Delete all dream timeline events (preserves chat summaries and email responses)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"DELETE DREAM EVENTS\n"
            f"{'='*60}\n"
        ))

        self.stdout.write(f"Dry run: {dry_run}\n")

        # Count dream events
        dream_events = TimelineEvent.objects.filter(kind='dream')
        count = dream_events.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No dream events found to delete."))
            return

        self.stdout.write(f"\nFound {count} dream events to delete.\n")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "[DRY RUN] Would delete the following:\n"
            ))

            # Show sample of what would be deleted
            sample = dream_events[:10]
            for event in sample:
                summary = event.data.get('dream_summary', event.data.get('dream_text', 'N/A'))[:50]
                self.stdout.write(f"  - {event.event_id}: {summary}...")

            if count > 10:
                self.stdout.write(f"  ... and {count - 10} more\n")

            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would delete {count} dream events total.\n"
            ))
            return

        # Confirm deletion
        self.stdout.write(self.style.WARNING(
            f"\nThis will permanently delete {count} dream events.\n"
            f"Chat summaries and email responses will be preserved.\n"
        ))

        confirm = input("Are you sure you want to continue? (yes/no): ")

        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR("Deletion cancelled."))
            return

        # Delete dream events
        deleted_count, _ = dream_events.delete()

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"SUMMARY\n"
            f"{'='*60}\n"
            f"Deleted {deleted_count} dream events.\n"
            f"{'='*60}\n"
        ))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Dream events deleted successfully!\n"
            f"You can now run: python manage.py backfill_timeline\n"
        ))
