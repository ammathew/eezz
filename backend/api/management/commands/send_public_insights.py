"""
Management command to manually send follow-up insights to public dream submission users.
Useful for testing and debugging the public user email system.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import sys

from api.models import PublicDreamSubmission
from dream_brain.tasks import send_public_user_insights


class Command(BaseCommand):
    help = 'Send follow-up insights to public dream submission users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Send insight to a specific email address (for testing)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which submissions would receive emails without actually sending',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send even if not due (useful for testing)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of insights to send',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        email_filter = options.get('email')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        limit = options.get('limit')
        skip_confirm = options.get('yes', False)

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('PUBLIC USER FOLLOW-UP INSIGHTS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Use the generator to find emails (deduped)
        from api.services.public_insight_generator import PublicInsightGenerator
        generator = PublicInsightGenerator()

        # If specific email is provided, filter
        if email_filter:
            self.stdout.write(f"Filtering to email: {email_filter}")
            email_groups = generator.find_emails_for_insight(force=force)
            email_groups = [g for g in email_groups if g['email'] == email_filter]
        else:
            # Find all eligible emails (deduped)
            email_groups = generator.find_emails_for_insight(force=force)

        # Apply limit if specified
        if limit:
            email_groups = email_groups[:limit]

        self.stdout.write(f"Found {len(email_groups)} unique email(s)")
        total_dreams = sum(len(g['submissions']) for g in email_groups)
        self.stdout.write(f"Total dreams across all emails: {total_dreams}")
        self.stdout.write('')

        if not email_groups:
            self.stdout.write(self.style.WARNING("No eligible emails found."))
            return

        # Show email details
        for i, group in enumerate(email_groups, 1):
            self.stdout.write(f"{i}. {group['email']} ({len(group['submissions'])} dream(s))")
            for sub in group['submissions']:
                self.stdout.write(f"   - Submission {sub.submission_id}: {sub.dream_text[:50]}...")
            self.stdout.write(f"   Last insight sent: {group['submissions'][0].last_insight_sent_at or 'Never'}")
            self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No emails will be sent"))
            return

        # Confirm before sending
        if not email_filter and not force and not skip_confirm:
            confirm = input(f"\nSend insights to {len(email_groups)} user(s)? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING("Cancelled."))
                return

        # Send insights using the scheduled task
        self.stdout.write(self.style.SUCCESS(f"\nSending insights...\n"))

        # If email filter, force mode, or limit specified, we need to run our own logic
        # Otherwise, use the task
        if email_filter or force or limit:
            from emails.services.base import BaseEmailService
            import markdown
            from django.conf import settings

            email_service = BaseEmailService()
            sent_count = 0
            failed_count = 0

            total_emails = len(email_groups)
            for idx, email_group in enumerate(email_groups, 1):
                email = email_group['email']
                submissions = email_group['submissions']

                try:
                    self.stdout.write(f"[{idx}/{total_emails}] Processing {email} ({len(submissions)} dream(s))...")

                    # Generate insight with ALL dreams
                    insight_data = generator.generate_insight_content(submissions)

                    if not insight_data:
                        self.stdout.write(self.style.ERROR(f"  Failed to generate insight"))
                        failed_count += 1
                        continue

                    # Convert markdown to HTML
                    content_html = markdown.markdown(
                        insight_data['content'],
                        extensions=['extra']
                    )

                    # Build URLs
                    first_submission = submissions[0]
                    signup_url = f"{settings.FRONTEND_URL}/signup?email={email}"
                    unsubscribe_url = f"{settings.FRONTEND_URL}/public-unsubscribe/{first_submission.unsubscribe_token}"

                    # Send email
                    email_sent = email_service.send(
                        user=None,
                        recipient_email=email,
                        subject=insight_data['subject'],
                        template_name='emails/public_user_insight.html',
                        context={
                            'subject': insight_data['subject'],
                            'insight_content': content_html,
                            'signup_url': signup_url,
                            'unsubscribe_url': unsubscribe_url,
                        },
                        email_type='public-followup',
                    )

                    if email_sent:
                        # Update ALL submissions from this email
                        now = timezone.now()
                        for sub in submissions:
                            sub.last_insight_sent_at = now
                            sub.save(update_fields=['last_insight_sent_at'])
                        sent_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Sent"))
                    else:
                        # Email failed - unsubscribe all submissions to prevent retries
                        for sub in submissions:
                            sub.email_subscribed = False
                            sub.save(update_fields=['email_subscribed'])
                        failed_count += 1
                        self.stdout.write(self.style.ERROR(f"  ✗ Failed to send - unsubscribed to prevent retries"))

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('SUMMARY'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(f"Total unique emails: {len(email_groups)}")
            self.stdout.write(self.style.SUCCESS(f"Successfully sent: {sent_count}"))
            if failed_count > 0:
                self.stdout.write(self.style.ERROR(f"Failed: {failed_count}"))
        else:
            # Run the scheduled task
            result = send_public_user_insights()

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('TASK RESULT'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(f"Status: {result.get('status')}")
            self.stdout.write(f"Unique emails: {result.get('emails_sent', 0)}")
            self.stdout.write(self.style.SUCCESS(f"Successfully sent: {result.get('sent', 0)}"))
            if result.get('failed', 0) > 0:
                self.stdout.write(self.style.ERROR(f"Failed: {result.get('failed', 0)}"))
