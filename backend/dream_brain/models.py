from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import Conversation
from emails.models import Email
import uuid


class DailyInsight(models.Model):
    """
    Daily personalized insight email based on user's entire Dream Brain.
    Sent once per day, analyzes all dreams, symbols, patterns, responses.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    # Tracking
    insight_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_insights'
    )
    email = models.OneToOneField(
        Email,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_insight'
    )

    # Content
    subject = models.CharField(max_length=255)
    content = models.TextField(help_text="AI-generated daily insight content")
    reply_to_email = models.EmailField(help_text="Unique reply-to for tracking responses")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Daily Insight for {self.user.email} on {self.created_at.date()}"


class DailyInsightResponse(models.Model):
    """
    User's email reply to a daily insight.
    """
    # Tracking
    response_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Relationships
    daily_insight = models.ForeignKey(
        DailyInsight,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_insight_responses'
    )

    # Content
    raw_content = models.TextField(help_text="Raw email reply content")
    cleaned_content = models.TextField(help_text="Cleaned/parsed reply content")

    # Processing
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(null=True, blank=True)

    # Timestamps
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['user', 'processed', 'received_at']),
            models.Index(fields=['daily_insight', 'received_at']),
        ]

    def __str__(self):
        return f"Daily Insight Response from {self.user.email} on {self.received_at.date()}"


class TimelineEvent(models.Model):
    """
    Timeline of distilled story events for a user's dream journey.
    Contains only the important checkpoints, not full chat logs.
    This is the spine that the LLM uses to understand the user's dream narrative.
    """
    EVENT_KIND_CHOICES = [
        ('dream', 'Dream'),
        ('chat_summary', 'Chat Summary'),
        ('email_response_summary', 'Email Response Summary'),
    ]

    # Tracking
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    dream = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='timeline_events',
        help_text="Optional: link to the dream conversation this event is about"
    )

    # Event data
    kind = models.CharField(max_length=30, choices=EVENT_KIND_CHOICES, db_index=True)
    at = models.DateTimeField(default=timezone.now, db_index=True, help_text="When this event occurred")
    data = models.JSONField(
        default=dict,
        help_text="Concise structured info. E.g., {'dream_text': '...', 'themes': [...]} or {'summary': '...', 'key_points': [...]}"
    )

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-at']
        indexes = [
            models.Index(fields=['user', '-at']),
            models.Index(fields=['user', 'kind', '-at']),
            models.Index(fields=['dream', '-at']),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} for {self.user.email} at {self.at.date()}"
