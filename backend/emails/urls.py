"""
URLs for email webhooks.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Postmark webhooks
    path('webhooks/postmark/inbound/', views.postmark_inbound_webhook, name='postmark_inbound_webhook'),
    path('webhooks/postmark/events/', views.postmark_event_webhook, name='postmark_event_webhook'),
]
