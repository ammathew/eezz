from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .ad_views import generate_ad, post_to_facebook, launch_facebook_ad
from .facebook_views import facebook_login_url, facebook_connect, facebook_status
from .oauth_views import GoogleLogin, GoogleLoginRedirect, google_callback
from .public_views import submit_dream, submit_email, unsubscribe
from .stripe_views import (
    stripe_webhook,
    create_checkout_session,
    create_portal_session,
    subscription_status
)
from .admin_views import (
    LoginAsUserView,
    ListUsersView,
    StartHijackSessionView,
    EndHijackSessionView,
    RefreshHijackSessionView
)
from .analytics_views import (
    analytics_overview,
    analytics_signups_over_time,
    analytics_email_engagement,
    analytics_public_funnel,
    analytics_user_retention,
    analytics_top_users
)

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('auth/google/', GoogleLoginRedirect.as_view(), name='google_login_redirect'),
    path('auth/google/login/', GoogleLogin.as_view(), name='google_login'),
    path('auth/google/callback/', google_callback, name='google_callback'),
    # Admin endpoints
    path('admin/users/', ListUsersView.as_view(), name='list_users'),
    path('admin/hijack/start/<int:user_id>/', StartHijackSessionView.as_view(), name='start_hijack'),
    path('admin/hijack/refresh/', RefreshHijackSessionView.as_view(), name='refresh_hijack'),
    path('admin/hijack/end/', EndHijackSessionView.as_view(), name='end_hijack'),
    path('auth/login-as-user/<int:user_id>/', LoginAsUserView.as_view(), name='login_as_user'),  # Deprecated
    # Public dream submission endpoints
    path('public/submit-dream/', submit_dream, name='submit_dream'),
    path('public/submit-email/', submit_email, name='submit_email'),
    path('public/unsubscribe/<uuid:token>/', unsubscribe, name='unsubscribe'),
    # Stripe subscription endpoints
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    path('subscription/create-checkout/', create_checkout_session, name='create_checkout'),
    path('subscription/create-portal/', create_portal_session, name='create_portal'),
    path('subscription/status/', subscription_status, name='subscription_status'),
    # Email preferences
    path('preferences/email/', views.get_email_preferences, name='get_email_preferences'),
    path('preferences/email/update/', views.update_email_preferences, name='update_email_preferences'),
    # Ad generator endpoints
    path('ads/generate/', generate_ad, name='generate_ad'),
    path('ads/post/', post_to_facebook, name='post_to_facebook'),
    path('ads/launch/', launch_facebook_ad, name='launch_facebook_ad'),
    # Facebook OAuth endpoints
    path('facebook/login-url/', facebook_login_url, name='facebook_login_url'),
    path('facebook/connect/', facebook_connect, name='facebook_connect'),
    path('facebook/status/', facebook_status, name='facebook_status'),
    # Analytics endpoints
    path('analytics/overview/', analytics_overview, name='analytics_overview'),
    path('analytics/signups/', analytics_signups_over_time, name='analytics_signups'),
    path('analytics/email-engagement/', analytics_email_engagement, name='analytics_email_engagement'),
    path('analytics/public-funnel/', analytics_public_funnel, name='analytics_public_funnel'),
    path('analytics/user-retention/', analytics_user_retention, name='analytics_user_retention'),
    path('analytics/top-users/', analytics_top_users, name='analytics_top_users'),
    path('', include(router.urls)),
]
