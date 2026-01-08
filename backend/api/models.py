from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import uuid


class Conversation(models.Model):
    """Represents a chat conversation"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,  # Allow null for existing conversations
        blank=True
    )
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Message(models.Model):
    """Represents a message in a conversation"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class DreamSymbol(models.Model):
    """Represents a dream symbol interpretation"""
    SOURCE_CHOICES = [
        ('dreammoods', 'DreamMoods'),
    ]

    keyword = models.TextField()
    interpretation = models.TextField()
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='dreammoods')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['keyword']
        indexes = [
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return f"{self.keyword[:50]} ({self.source})"


class UserProfile(models.Model):
    """Represents a user's profile with additional details"""

    EMAIL_FREQUENCY_CHOICES = [
        ('off', 'Off - No emails'),
        ('daily', 'Daily'),
        ('every_2_days', 'Every 2 days'),
        ('every_3_days', 'Every 3 days'),
        ('every_5_days', 'Every 5 days'),
        ('weekly', 'Weekly'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    picture = models.URLField(max_length=2048, blank=True, null=True, help_text="Profile picture URL from OAuth provider")
    token_limit = models.IntegerField(default=100000, help_text="Maximum tokens allowed per month")
    is_locked = models.BooleanField(default=False, help_text="Account locked due to token limit")
    trial_ends_at = models.DateTimeField(null=True, blank=True, help_text="When the 14-day free trial ends")

    # Email preferences
    email_frequency = models.CharField(
        max_length=20,
        choices=EMAIL_FREQUENCY_CHOICES,
        default='daily',
        help_text="How often to receive daily insight emails"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_trial_active(self):
        """Check if user is still in trial period"""
        if not self.trial_ends_at:
            return False
        return timezone.now() < self.trial_ends_at

    def has_active_subscription(self):
        """Check if user has an active paid subscription"""
        return hasattr(self, 'user') and self.user.subscriptions.filter(
            status__in=['active', 'trialing']
        ).exists()

    def can_use_service(self):
        """Check if user can use the service (trial or paid)"""
        return self.is_trial_active() or self.has_active_subscription()


class TokenUsage(models.Model):
    """Tracks token usage for a user"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='token_usage'
    )
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    message = models.ForeignKey(
        'Message',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    input_tokens = models.IntegerField(default=0, help_text="Tokens in user's prompt")
    output_tokens = models.IntegerField(default=0, help_text="Tokens in AI response")
    tokens_used = models.IntegerField(default=0, help_text="Total tokens (input + output)")
    model_name = models.CharField(max_length=100, default='gemini-2.5-flash')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Token usage for {self.user.username} at {self.created_at}"


class Subscription(models.Model):
    """Tracks Stripe subscription details for a user"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('trialing', 'Trialing'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True, help_text="Stripe customer ID")
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Stripe subscription ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.status}"


class PublicDreamSubmission(models.Model):
    """Represents a public dream submission for lead generation"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),  # Skipped because user already has app account with conversations
    ]

    submission_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    dream_text = models.TextField()
    email = models.EmailField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    interpretation = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    # Email subscription fields
    email_subscribed = models.BooleanField(default=True, help_text="Whether user is subscribed to follow-up emails")
    last_insight_sent_at = models.DateTimeField(null=True, blank=True, help_text="When the last follow-up insight email was sent")
    unsubscribe_token = models.UUIDField(null=True, blank=True, editable=False, unique=True, help_text="Unique token for unsubscribe link")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission_id']),
            models.Index(fields=['email']),
            models.Index(fields=['unsubscribe_token']),
            models.Index(fields=['email_subscribed']),
        ]

    def __str__(self):
        return f"Submission {self.submission_id} - {self.status}"


class HijackSession(models.Model):
    """
    Represents a superadmin hijacking a user's session.
    Stores session metadata without storing admin tokens client-side.
    """
    session_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    admin_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hijack_sessions_as_admin',
        help_text="The superadmin who initiated the hijack"
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hijack_sessions_as_target',
        help_text="The user being viewed"
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(help_text="When this hijack session expires")
    is_active = models.BooleanField(default=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_token', 'is_active']),
            models.Index(fields=['admin_user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.admin_user.email} viewing {self.target_user.email}"

    def save(self, *args, **kwargs):
        # Set expiration to 15 minutes from creation if not set (security: shorter window)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def refresh_expiry(self):
        """Extend the hijack session by another 15 minutes"""
        self.expires_at = timezone.now() + timedelta(minutes=15)
        self.save()

    def is_expired(self):
        """Check if the hijack session has expired"""
        return timezone.now() > self.expires_at

    def end_session(self):
        """Mark the hijack session as ended"""
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()


class FacebookConnection(models.Model):
    """Stores Facebook OAuth connection details for a user."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='facebook_connection'
    )
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(null=True, blank=True)
    page_id = models.CharField(max_length=64, blank=True)
    page_name = models.CharField(max_length=255, blank=True)
    page_access_token = models.TextField(blank=True)
    ad_account_id = models.CharField(max_length=64, blank=True)
    ad_account_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Facebook Connection"
