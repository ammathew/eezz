"""
Management command to backfill timeline events from existing dream conversations.

This creates timeline events for dreams that were logged before the timeline system existed.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dream_brain.models import TimelineEvent
from dream_brain.services.timeline_service import TimelineService
from api.models import Conversation


class Command(BaseCommand):
    help = 'Backfill timeline events from existing dream conversations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email of specific user to backfill (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating events',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        user_email = options.get('user')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No events will be created'))

        # Filter users
        if user_email:
            users = User.objects.filter(email=user_email)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
                return
        else:
            users = User.objects.all()

        total_dreams_processed = 0
        total_events_created = 0

        for user in users:
            self.stdout.write(f'\nProcessing user: {user.email}')

            # Get all conversations for this user
            conversations = user.conversations.all().order_by('created_at')

            if not conversations.exists():
                self.stdout.write(f'  No dreams found for {user.email}')
                continue

            for conv in conversations:
                # Check if dream event already exists
                existing_dream_event = TimelineEvent.objects.filter(
                    user=user,
                    dream=conv,
                    kind='dream'
                ).exists()

                if not existing_dream_event:
                    # Create dream events (may create multiple if user shared multiple dreams)
                    if not dry_run:
                        dream_events = TimelineService.create_dream_events(user, conv)
                        if dream_events:
                            total_events_created += len(dream_events)
                            for event in dream_events:
                                self.stdout.write(
                                    self.style.SUCCESS(f'  Created dream event: {event.event_id}')
                                )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  Failed to create dream events for conversation {conv.id}')
                            )
                    else:
                        self.stdout.write(f'  [DRY RUN] Would create dream events for conversation {conv.id}')
                        total_events_created += 1

                # Check if we should create a chat summary
                # Only create if there are multiple messages (indicating a conversation happened)
                message_count = conv.messages.count()
                if message_count > 1:
                    existing_summary = TimelineEvent.objects.filter(
                        user=user,
                        dream=conv,
                        kind='chat_summary'
                    ).exists()

                    if not existing_summary:
                        if not dry_run:
                            summary_event = TimelineService.create_chat_summary_event(user, conv)
                            if summary_event:
                                total_events_created += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'  Created chat summary: {summary_event.event_id}')
                                )
                            else:
                                self.stdout.write(
                                    self.style.WARNING(f'  Failed to create chat summary for conversation {conv.id}')
                                )
                        else:
                            self.stdout.write(f'  [DRY RUN] Would create chat summary for conversation {conv.id}')
                            total_events_created += 1

                total_dreams_processed += 1

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Total dreams processed: {total_dreams_processed}'))
        self.stdout.write(self.style.SUCCESS(f'Total events created: {total_events_created}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN. Run without --dry-run to actually create events.'))
