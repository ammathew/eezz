from django.contrib import admin
from .models import DailyInsight, DailyInsightResponse, TimelineEvent


@admin.register(DailyInsight)
class DailyInsightAdmin(admin.ModelAdmin):
    list_display = ['insight_id', 'user', 'subject', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'subject', 'insight_id']
    readonly_fields = ['insight_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(DailyInsightResponse)
class DailyInsightResponseAdmin(admin.ModelAdmin):
    list_display = ['response_id', 'user', 'daily_insight', 'processed', 'received_at']
    list_filter = ['processed', 'received_at']
    search_fields = ['user__email', 'response_id', 'cleaned_content']
    readonly_fields = ['response_id', 'received_at', 'processed_at']
    date_hierarchy = 'received_at'

    fieldsets = (
        ('Basic Info', {
            'fields': ('response_id', 'user', 'daily_insight')
        }),
        ('Content', {
            'fields': ('raw_content', 'cleaned_content')
        }),
        ('Processing', {
            'fields': ('processed', 'processed_at', 'processing_error')
        }),
        ('Timestamps', {
            'fields': ('received_at',)
        }),
    )


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'user', 'kind', 'dream', 'at', 'created_at']
    list_filter = ['kind', 'at', 'created_at']
    search_fields = ['user__email', 'event_id', 'data']
    readonly_fields = ['event_id', 'created_at']
    date_hierarchy = 'at'

    fieldsets = (
        ('Basic Info', {
            'fields': ('event_id', 'user', 'dream', 'kind', 'at')
        }),
        ('Event Data', {
            'fields': ('data',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
