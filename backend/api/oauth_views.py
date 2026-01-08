from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.shortcuts import redirect
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse
from django.views import View
import os


def get_base_url(request=None):
    """Get the base URL based on environment and request"""
    if settings.DEBUG:
        return "http://localhost:8000"

    # In production, use the host from the request if available
    if request:
        host = request.get_host()
        return f"https://{host}"

    # Fallback to eezz.ad
    return "https://eezz.ad"


def get_frontend_url(request=None):
    """Get the frontend URL based on environment and request"""
    if settings.DEBUG:
        return "http://localhost:5173"

    # In production, use the host from the request if available
    if request:
        host = request.get_host()
        return f"https://{host}"

    # Fallback to eezz.ad
    return "https://eezz.ad"


class GoogleLogin(SocialLoginView):
    """
    Google OAuth2 login view that returns JWT tokens
    """
    adapter_class = GoogleOAuth2Adapter

    @property
    def callback_url(self):
        return f"{get_base_url(self.request)}/api/auth/google/callback/"

    client_class = OAuth2Client


class GoogleLoginRedirect(View):
    """
    Redirect to Google OAuth login
    """
    def get(self, request):
        from allauth.socialaccount.models import SocialApp
        from urllib.parse import urlencode
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Get Google OAuth app credentials
            try:
                google_app = SocialApp.objects.get(provider='google')
                client_id = google_app.client_id
                logger.info(f"Using Google OAuth client_id from database: {client_id[:10]}...")
            except SocialApp.DoesNotExist:
                client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
                logger.info(f"Using Google OAuth client_id from settings: {client_id[:10] if client_id else 'NONE'}...")

            if not client_id:
                error_msg = "Google OAuth not configured. Please set GOOGLE_OAUTH_CLIENT_ID environment variable."
                logger.error(error_msg)
                return HttpResponse(error_msg, status=500)

            # Build Google OAuth URL
            base_url = get_base_url(request)
            callback_uri = f"{base_url}/api/auth/google/callback/"

            logger.info(f"Request host: {request.get_host()}")
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Callback URI: {callback_uri}")

            params = {
                'client_id': client_id,
                'redirect_uri': callback_uri,
                'scope': 'openid email profile',
                'response_type': 'code',
                'access_type': 'online',
            }

            google_auth_url = f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}'
            logger.info(f"Redirecting to Google OAuth URL")
            return redirect(google_auth_url)

        except Exception as e:
            logger.error(f"Error in GoogleLoginRedirect: {str(e)}", exc_info=True)
            return HttpResponse(f"Error: {str(e)}", status=500)


def google_callback(request):
    """
    Handle Google OAuth callback and redirect to frontend with tokens
    """
    import requests
    from django.contrib.auth import get_user_model
    from allauth.socialaccount.models import SocialApp

    code = request.GET.get('code')
    if not code:
        return redirect(f"{get_frontend_url(request)}/")

    try:
        # Get Google OAuth credentials
        try:
            google_app = SocialApp.objects.get(provider='google')
            client_id = google_app.client_id
            client_secret = google_app.secret
        except SocialApp.DoesNotExist:
            client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
            client_secret = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret']

        # Exchange code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': f"{get_base_url(request)}/api/auth/google/callback/",
            'grant_type': 'authorization_code',
        }

        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        if 'access_token' not in token_json:
            return redirect(f"{get_frontend_url(request)}/")

        # Get user info from Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f"Bearer {token_json['access_token']}"}
        )
        user_info = user_info_response.json()

        # Get or create user
        User = get_user_model()
        email = user_info.get('email')

        # Try to get existing user, handle duplicates
        try:
            user = User.objects.get(email=email)
            created = False
        except User.MultipleObjectsReturned:
            # Handle duplicate users - use the first one and log warning
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Multiple users found with email {email}. Using the first one.")
            user = User.objects.filter(email=email).first()
            created = False
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                email=email,
                username=email,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
            )
            created = True

        # Update or create user profile with picture and trial period
        from .models import UserProfile
        from datetime import timedelta
        profile, profile_created = UserProfile.objects.get_or_create(user=user)

        # Set trial period for new users (14 days)
        if profile_created and not profile.trial_ends_at:
            profile.trial_ends_at = timezone.now() + timedelta(days=14)

        # Update picture from Google
        picture_url = user_info.get('picture')
        if picture_url:
            profile.picture = picture_url

        profile.save()

        # Update user name if it changed
        if not created:
            updated = False
            if user.first_name != user_info.get('given_name', ''):
                user.first_name = user_info.get('given_name', '')
                updated = True
            if user.last_name != user_info.get('family_name', ''):
                user.last_name = user_info.get('family_name', '')
                updated = True
            if updated:
                user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Redirect to frontend with tokens
        frontend_url = f"{get_frontend_url(request)}/auth/callback?access={access_token}&refresh={refresh_token}"
        return redirect(frontend_url)

    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect(f"{get_frontend_url(request)}/")
