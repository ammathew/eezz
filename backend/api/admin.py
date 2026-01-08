from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, Message, PublicDreamSubmission, UserProfile, Subscription, TokenUsage, HijackSession


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ['role', 'content', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['created_at']
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_email', 'title', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'user__email', 'user__username']
    inlines = [MessageInline]
    readonly_fields = ['created_at', 'updated_at']

    def user_email(self, obj):
        return obj.user.email if obj.user else 'Anonymous'
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_title', 'user_email', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__title', 'conversation__user__email']
    readonly_fields = ['created_at']

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'

    def conversation_title(self, obj):
        return obj.conversation.title
    conversation_title.short_description = 'Conversation'

    def user_email(self, obj):
        return obj.conversation.user.email if obj.conversation.user else 'Anonymous'
    user_email.short_description = 'User'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'trial_status', 'trial_ends_at', 'token_limit', 'is_locked', 'created_at']
    list_filter = ['is_locked', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def trial_status(self, obj):
        if obj.is_trial_active():
            return format_html('<span style="color: green;">Active</span>')
        elif obj.has_active_subscription():
            return format_html('<span style="color: blue;">Subscribed</span>')
        else:
            return format_html('<span style="color: red;">Expired</span>')
    trial_status.short_description = 'Status'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'status', 'stripe_customer_id', 'current_period_end', 'cancel_at_period_end', 'created_at']
    list_filter = ['status', 'cancel_at_period_end', 'created_at']
    search_fields = ['user__email', 'stripe_customer_id', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'


@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'tokens_used', 'input_tokens', 'output_tokens', 'model_name', 'created_at']
    list_filter = ['model_name', 'created_at']
    search_fields = ['user__email', 'conversation__title']
    readonly_fields = ['created_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'


@admin.register(PublicDreamSubmission)
class PublicDreamSubmissionAdmin(admin.ModelAdmin):
    list_display = ['submission_id', 'email', 'status', 'created_at', 'email_sent_at']
    list_filter = ['status', 'created_at', 'email_sent_at']
    search_fields = ['email', 'submission_id', 'dream_text']
    readonly_fields = ['submission_id', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(HijackSession)
class HijackSessionAdmin(admin.ModelAdmin):
    list_display = ['session_token_short', 'admin_email', 'target_email', 'is_active', 'created_at', 'expires_at', 'ip_address']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['admin_user__email', 'target_user__email', 'session_token', 'ip_address']
    readonly_fields = ['session_token', 'admin_user', 'target_user', 'created_at', 'expires_at', 'ended_at', 'ip_address', 'user_agent']
    ordering = ['-created_at']

    def session_token_short(self, obj):
        return str(obj.session_token)[:8] + '...'
    session_token_short.short_description = 'Session'

    def admin_email(self, obj):
        return obj.admin_user.email
    admin_email.short_description = 'Admin'
    admin_email.admin_order_field = 'admin_user__email'

    def target_email(self, obj):
        return obj.target_user.email
    target_email.short_description = 'Target User'
    target_email.admin_order_field = 'target_user__email'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('admin_user', 'target_user')
