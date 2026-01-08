from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Email(models.Model):
    """
    Tracks every email sent through the system.
    Central model for all email communications.
    """
    EMAIL_TYPE_CHOICES = [
        ('public-interpretation', 'Public Interpretation'),  # Public dream interpretations
        ('public-followup', 'Public Follow-up'),             # Public user follow-up insights
        ('appuser-followup', 'App User Follow-up'),          # App user daily insights/reflections
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]

    # Tracking
    email_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Recipients
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_received',
        help_text="Associated user (if registered)"
    )
    recipient_email = models.EmailField(db_index=True)

    # Content
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255, help_text="Email template used")
    context_data = models.JSONField(default=dict, help_text="Template context data")

    # Metadata
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES, default='public-interpretation', db_index=True)
    reply_to_email = models.EmailField(null=True, blank=True, help_text="Custom reply-to address (for reflections)")
    from_email = models.EmailField(help_text="Sender email address")

    # Provider tracking
    provider_name = models.CharField(max_length=50, default='postmark', help_text="Email provider used")
    provider_message_id = models.CharField(max_length=255, null=True, blank=True, help_text="Provider's message ID")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'email_type', 'created_at']),
            models.Index(fields=['recipient_email', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.email_type}: {self.subject} → {self.recipient_email}"


class EmailEvent(models.Model):
    """
    Tracks email events: opens, clicks, bounces, spam reports.
    Populated by webhook callbacks from email provider.
    """
    EVENT_TYPE_CHOICES = [
        ('open', 'Opened'),
        ('click', 'Clicked'),
        ('bounce', 'Bounced'),
        ('spam', 'Marked as Spam'),
        ('unsubscribe', 'Unsubscribed'),
        ('reply', 'Replied'),
    ]

    email = models.ForeignKey(
        Email,
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, db_index=True)
    event_data = models.JSONField(default=dict, help_text="Raw event data from provider")

    # For click events
    clicked_url = models.URLField(null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'event_type']),
            models.Index(fields=['event_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.email.subject}"


class InboundEmail(models.Model):
    """
    Stores inbound email replies (e.g., replies to reflection emails).
    Populated by webhook from email provider's inbound parser.
    """
    # Tracking
    inbound_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Link to original outbound email (if we can match it)
    original_email = models.ForeignKey(
        Email,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Original email this is replying to"
    )

    # Sender info
    sender_email = models.EmailField(db_index=True)
    sender_name = models.CharField(max_length=255, blank=True)

    # Content
    subject = models.CharField(max_length=500)
    text_content = models.TextField(help_text="Plain text body")
    html_content = models.TextField(blank=True, help_text="HTML body")

    # Metadata
    recipient_email = models.EmailField(help_text="Which of our emails it was sent to")
    headers = models.JSONField(default=dict, help_text="Email headers")
    raw_data = models.JSONField(default=dict, help_text="Raw webhook data")

    # Processing
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(null=True, blank=True)

    # Timestamps
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['sender_email', 'received_at']),
            models.Index(fields=['processed', 'received_at']),
            models.Index(fields=['original_email', 'received_at']),
        ]

    def __str__(self):
        return f"Reply from {self.sender_email}: {self.subject[:50]}"


class EmailTemplate(models.Model):
    """
    Optional: Store email templates in DB for non-technical editing.
    For now, we'll use Django templates, but this allows future flexibility.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    subject_template = models.CharField(max_length=255)
    html_template = models.TextField()
    text_template = models.TextField()

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
