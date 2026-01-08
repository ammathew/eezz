# -*- coding: utf-8 -*-
"""
Management command to test the full reflection sequence for a specific user.
Resets their reflections and sends all 3 in sequence.

Usage:
    python manage.py test_reflection_sequence --user sunship.space@gmail.com
    python manage.py test_reflection_sequence --user sunship.space@gmail.com --dry-run
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
import logging

from dream_brain.services.reflection_generator import ReflectionGenerator
from dream_brain.models import Reflection
from emails.services.base import BaseEmailService
from emails.models import Email
import markdown

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test full reflection sequence for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='User email address'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Generate reflections but do not send emails'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of reflections to send (1, 2, or 3)'
        )

    def handle(self, *args, **options):
        user_email = options['user']
        dry_run = options['dry_run']
        count = min(max(options['count'], 1), 3)  # Clamp between 1 and 3

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"REFLECTION SEQUENCE TEST\n"
            f"Sending {count} reflection email{'s' if count > 1 else ''} for one user\n"
            f"{'='*60}\n"
        ))

        # Find user
        try:
            user = User.objects.get(email=user_email)
            self.stdout.write(self.style.SUCCESS(f"✓ Found user: {user.username} ({user.email})"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ User not found: {user_email}"))
            return

        # Get their last conversation
        last_conversation = user.conversations.order_by('-created_at').first()
        if not last_conversation:
            self.stdout.write(self.style.ERROR(f"✗ No conversations found for user"))
            return

        self.stdout.write(f"✓ Found last dream (ID: {last_conversation.id})")
        self.stdout.write(f"  Created: {last_conversation.created_at}")

        # Reset reflections for this user
        self.stdout.write(self.style.WARNING("\n[Step 1] Resetting reflections for this user..."))

        # Get reflection emails to delete
        reflection_ids = Reflection.objects.filter(user=user).values_list('email_id', flat=True)
        reflection_count = Reflection.objects.filter(user=user).count()

        # Delete reflections and their emails
        Reflection.objects.filter(user=user).delete()
        Email.objects.filter(id__in=reflection_ids).delete()

        self.stdout.write(f"✓ Deleted {reflection_count} existing reflections\n")

        # Initialize services
        generator = ReflectionGenerator()
        email_service = BaseEmailService()

        # Generate and send all 3 reflections
        self.stdout.write(self.style.WARNING("[Step 2] Generating and sending reflections...\n"))

        sent_count = 0
        failed_count = 0

        for reflection_number in range(1, count + 1):
            self.stdout.write(f"  → Reflection #{reflection_number}...")

            try:
                # Generate reflection
                reflection = generator.create_reflection(user, last_conversation, reflection_number)

                if not reflection:
                    self.stdout.write(self.style.ERROR(f"    ✗ Failed to generate reflection #{reflection_number}"))
                    failed_count += 1
                    continue

                self.stdout.write(f"    ✓ Generated: {reflection.subject}")

                if dry_run:
                    self.stdout.write(self.style.WARNING(f"    ⚠ DRY RUN - Not sending\n"))
                    continue

                # Convert markdown content to HTML if needed
                content_html = markdown.markdown(
                    reflection.content,
                    extensions=['nl2br', 'fenced_code']
                )

                # Send email
                email = email_service.send(
                    user=reflection.user,
                    recipient_email=reflection.user.email,
                    subject=reflection.subject,
                    template_name='emails/reflection.html',
                    context={
                        'user_name': reflection.user.first_name or reflection.user.username,
                        'subject': reflection.subject,
                        'reflection_content': content_html,
                    },
                    email_type='appuser-followup',
                    reply_to=reflection.reply_to_email
                )

                if email:
                    # Update reflection record
                    reflection.email = email
                    reflection.status = 'sent'
                    reflection.sent_at = timezone.now()
                    reflection.save()

                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(f"    ✓ Sent successfully\n"))
                else:
                    reflection.status = 'failed'
                    reflection.failed_reason = "Email service returned None"
                    reflection.save()

                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f"    ✗ Failed to send\n"))

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f"    ✗ Error: {type(e).__name__}: {str(e)}\n"
                ))

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"SUMMARY\n"
            f"{'='*60}\n"
            f"User: {user.email}\n"
            f"Dream created: {last_conversation.created_at}\n"
        ))

        if dry_run:
            self.stdout.write(f"Mode: DRY RUN (no emails sent)\n")
        else:
            self.stdout.write(
                f"Successfully sent: {sent_count}/{count}\n"
                f"Failed: {failed_count}/{count}\n"
            )

        self.stdout.write(f"{'='*60}\n")

        if sent_count == count and not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ All {count} reflection email{'s' if count > 1 else ''} sent to {user.email}!\n"
            ))
