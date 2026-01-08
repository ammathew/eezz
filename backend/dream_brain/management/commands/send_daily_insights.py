# -*- coding: utf-8 -*-
"""
Management command to generate and send daily Dream Brain insights.

Usage:
    python manage.py send_daily_insights
    python manage.py send_daily_insights --limit 50
    python manage.py send_daily_insights --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from dream_brain.services.daily_insight_generator import DailyInsightGenerator
from emails.services.base import BaseEmailService
import markdown

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate and send daily Dream Brain insight emails to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of insights to send'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Generate insights but do not send emails'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Send only to specific user email'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        specific_user = options.get('user')

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"DREAM BRAIN - DAILY INSIGHTS\n"
            f"Personalized daily emails based on entire Dream Brain\n"
            f"{'='*60}\n"
        ))

        self.stdout.write(f"Limit: {limit}")
        self.stdout.write(f"Dry run: {dry_run}")
        if specific_user:
            self.stdout.write(f"Specific user: {specific_user}")
        self.stdout.write("")

        # Initialize services
        generator = DailyInsightGenerator()
        email_service = BaseEmailService()

        # Step 1: Generate insights
        self.stdout.write(self.style.WARNING("\\n[Step 1] Generating daily insights..."))

        if specific_user:
            # Generate for specific user
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(email=specific_user)
                daily_insight = generator.create_daily_insight(user)
                insights = [daily_insight] if daily_insight else []
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User not found: {specific_user}"))
                return
        else:
            # Generate for all eligible users
            insights = generator.generate_daily_insights_batch(limit)

        if not insights:
            self.stdout.write(self.style.WARNING("No insights to send."))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Generated {len(insights)} insights\\n"
        ))

        # Step 2: Send emails
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "[Step 2] DRY RUN - Not sending emails\\n"
            ))
            for insight in insights:
                self.stdout.write(
                    f"  Would send: {insight.subject} to {insight.user.email}"
                )
            return

        self.stdout.write(self.style.WARNING("\\n[Step 2] Sending emails..."))
        sent_count = 0
        failed_count = 0

        for insight in insights:
            try:
                # Convert markdown content to HTML
                content_html = markdown.markdown(
                    insight.content,
                    extensions=['extra']
                )

                # Send email
                email = email_service.send(
                    user=insight.user,
                    recipient_email=insight.user.email,
                    subject=insight.subject,
                    template_name='emails/daily_insight.html',
                    context={
                        'user_name': insight.user.first_name or insight.user.username,
                        'subject': insight.subject,
                        'insight_content': content_html,
                    },
                    email_type='appuser-followup',
                    reply_to=insight.reply_to_email
                )

                if email:
                    # Update insight record
                    insight.email = email
                    insight.status = 'sent'
                    insight.sent_at = timezone.now()
                    insight.save()

                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  Sent: {insight.subject} to {insight.user.email}"
                    ))
                else:
                    insight.status = 'failed'
                    insight.failed_reason = "Email service returned None"
                    insight.save()

                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"  Failed: {insight.subject} to {insight.user.email}"
                    ))

            except Exception as e:
                failed_count += 1
                insight.status = 'failed'
                insight.failed_reason = str(e)
                insight.save()

                self.stdout.write(self.style.ERROR(
                    f"  Error: {insight.user.email} - {type(e).__name__}: {str(e)}"
                ))

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\\n{'='*60}\\n"
            f"SUMMARY\\n"
            f"{'='*60}\\n"
            f"Total insights generated: {len(insights)}\\n"
            f"Successfully sent: {sent_count}\\n"
            f"Failed: {failed_count}\\n"
            f"{'='*60}\\n"
        ))

        if sent_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"\\n{sent_count} daily Dream Brain insights sent successfully!"
            ))
