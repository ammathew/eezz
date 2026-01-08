from django.contrib import admin
from .models import Email, EmailEvent, InboundEmail, EmailTemplate


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['email_id', 'recipient_email', 'subject', 'email_type', 'status', 'sent_at', 'created_at']
    list_filter = ['email_type', 'status', 'provider_name', 'created_at']
    search_fields = ['recipient_email', 'subject', 'email_id']
    readonly_fields = ['email_id', 'created_at', 'updated_at', 'sent_at', 'delivered_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Info', {
            'fields': ('email_id', 'user', 'recipient_email', 'subject')
        }),
        ('Email Details', {
            'fields': ('template_name', 'context_data', 'email_type', 'from_email', 'reply_to_email')
        }),
        ('Provider & Status', {
            'fields': ('provider_name', 'provider_message_id', 'status', 'sent_at', 'delivered_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(EmailEvent)
class EmailEventAdmin(admin.ModelAdmin):
    list_display = ['email', 'event_type', 'clicked_url', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['email__recipient_email', 'clicked_url']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(InboundEmail)
class InboundEmailAdmin(admin.ModelAdmin):
    list_display = ['inbound_id', 'sender_email', 'subject', 'processed', 'received_at']
    list_filter = ['processed', 'received_at']
    search_fields = ['sender_email', 'subject', 'inbound_id']
    readonly_fields = ['inbound_id', 'received_at', 'processed_at']
    date_hierarchy = 'received_at'

    fieldsets = (
        ('Basic Info', {
            'fields': ('inbound_id', 'original_email', 'sender_email', 'sender_name', 'recipient_email')
        }),
        ('Content', {
            'fields': ('subject', 'text_content', 'html_content')
        }),
        ('Metadata', {
            'fields': ('headers', 'raw_data')
        }),
        ('Processing', {
            'fields': ('processed', 'processed_at', 'processing_error')
        }),
        ('Timestamps', {
            'fields': ('received_at',)
        }),
    )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
