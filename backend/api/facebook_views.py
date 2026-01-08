import logging
from datetime import timedelta

import requests
from decouple import config
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import FacebookConnection
from .dev_auth import resolve_request_user

logger = logging.getLogger(__name__)

FB_API_VERSION = 'v19.0'


class FacebookPermissionError(RuntimeError):
    pass


def _get_facebook_app_config():
    app_id = config('FB_APP_ID', default='').strip()
    app_secret = config('FB_APP_SECRET', default='').strip()
    if not app_id or not app_secret:
        raise ValueError('FB_APP_ID and FB_APP_SECRET must be configured')
    return app_id, app_secret


def _exchange_code_for_token(code, redirect_uri):
    app_id, app_secret = _get_facebook_app_config()
    url = f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token"
    params = {
        'client_id': app_id,
        'client_secret': app_secret,
        'redirect_uri': redirect_uri,
        'code': code,
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _exchange_for_long_lived_token(short_token):
    app_id, app_secret = _get_facebook_app_config()
    url = f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_token,
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _fetch_pages(access_token):
    url = f"https://graph.facebook.com/{FB_API_VERSION}/me/accounts"
    params = {
        'access_token': access_token,
        'fields': 'id,name,access_token',
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json().get('data', [])


def _fetch_ad_accounts(access_token):
    url = f"https://graph.facebook.com/{FB_API_VERSION}/me/adaccounts"
    params = {
        'access_token': access_token,
        'fields': 'id,name,account_id',
    }
    response = requests.get(url, params=params, timeout=20)
    if response.status_code == 403:
        detail = None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            error = payload.get('error', {})
            message = error.get('message')
            code = error.get('code')
            subcode = error.get('error_subcode')
            detail_bits = [bit for bit in (message, f"code {code}" if code is not None else None, f"subcode {subcode}" if subcode is not None else None) if bit]
            if detail_bits:
                detail = " - ".join(detail_bits)
        if not detail:
            detail = response.text or 'Facebook API permission error'
        raise FacebookPermissionError(
            "Facebook ad account access denied. Ensure the user grants ads_read or ads_management."
            f" Details: {detail}"
        )
    response.raise_for_status()
    return response.json().get('data', [])


def _manual_ad_account(ad_account_id):
    raw = (ad_account_id or '').strip()
    if not raw:
        return None
    account_id = raw[4:] if raw.startswith('act_') else raw
    return {
        'id': raw if raw.startswith('act_') else f"act_{raw}",
        'account_id': account_id,
        'name': 'Manual ad account',
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def facebook_login_url(request):
    try:
        app_id, _app_secret = _get_facebook_app_config()
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    redirect_uri = request.query_params.get('redirect_uri')
    if not redirect_uri:
        frontend_url = config('FRONTEND_URL', default='').strip()
        if not frontend_url:
            return Response(
                {'error': 'FRONTEND_URL must be configured or pass redirect_uri'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        redirect_uri = f"{frontend_url.rstrip('/')}/facebook/callback"

    scope = ','.join([
        'public_profile',
        'pages_show_list',
        'pages_read_engagement',
        'pages_manage_posts',
        'ads_read',
        'ads_management',
    ])
    auth_url = (
        f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth"
        f"?client_id={app_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
    )

    return Response({'login_url': auth_url}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def facebook_connect(request):
    user = resolve_request_user(request)
    if not user:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    code = str(request.data.get('code', '')).strip()
    redirect_uri = str(request.data.get('redirect_uri', '')).strip()
    desired_page_id = str(request.data.get('page_id', '')).strip()
    desired_ad_account_id = str(request.data.get('ad_account_id', '')).strip()

    if not code or not redirect_uri:
        return Response(
            {'error': 'code and redirect_uri are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        short_token_response = _exchange_code_for_token(code, redirect_uri)
        short_token = short_token_response.get('access_token')
        if not short_token:
            return Response(
                {'error': 'Failed to exchange code for access token'},
                status=status.HTTP_502_BAD_GATEWAY
            )
        long_token_response = _exchange_for_long_lived_token(short_token)
        long_token = long_token_response.get('access_token', short_token)
        expires_in = long_token_response.get('expires_in')
    except requests.RequestException as exc:
        logger.error("Facebook token exchange failed", exc_info=True)
        return Response(
            {'error': f'Facebook token exchange failed: {str(exc)}'},
            status=status.HTTP_502_BAD_GATEWAY
        )
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        pages = _fetch_pages(long_token)
        ad_accounts = _fetch_ad_accounts(long_token)
    except FacebookPermissionError as exc:
        logger.warning("Facebook permission issue: %s", exc)
        return Response(
            {'error': str(exc)},
            status=status.HTTP_403_FORBIDDEN
        )
    except requests.RequestException as exc:
        logger.error("Facebook data fetch failed", exc_info=True)
        return Response(
            {'error': f'Failed to fetch Facebook data: {str(exc)}'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    page = None
    if desired_page_id:
        page = next((p for p in pages if p.get('id') == desired_page_id), None)
        if not page:
            return Response(
                {'error': 'Requested page_id not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
    elif pages:
        page = pages[0]

    ad_account = None
    if desired_ad_account_id:
        ad_account = next((a for a in ad_accounts if a.get('id') == desired_ad_account_id or a.get('account_id') == desired_ad_account_id), None)
        if not ad_account:
            manual_account = _manual_ad_account(desired_ad_account_id)
            if manual_account:
                logger.warning("Using manual ad account override: %s", manual_account.get('id'))
                ad_account = manual_account
                if manual_account not in ad_accounts:
                    ad_accounts.append(manual_account)
    elif ad_accounts:
        ad_account = ad_accounts[0]

    token_expires_at = None
    if expires_in:
        token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))

    connection, _created = FacebookConnection.objects.update_or_create(
        user=user,
        defaults={
            'access_token': long_token,
            'token_expires_at': token_expires_at,
            'page_id': (page or {}).get('id', ''),
            'page_name': (page or {}).get('name', ''),
            'page_access_token': (page or {}).get('access_token', ''),
            'ad_account_id': (ad_account or {}).get('id', ''),
            'ad_account_name': (ad_account or {}).get('name', ''),
        }
    )

    return Response({
        'connected': True,
        'page_id': connection.page_id,
        'page_name': connection.page_name,
        'ad_account_id': connection.ad_account_id,
        'ad_account_name': connection.ad_account_name,
        'pages': pages,
        'ad_accounts': ad_accounts,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def facebook_status(request):
    user = resolve_request_user(request)
    if not user:
        return Response({'connected': False}, status=status.HTTP_200_OK)
    connection = getattr(user, 'facebook_connection', None)
    if not connection:
        return Response({'connected': False}, status=status.HTTP_200_OK)
    return Response({
        'connected': True,
        'page_id': connection.page_id,
        'page_name': connection.page_name,
        'ad_account_id': connection.ad_account_id,
        'ad_account_name': connection.ad_account_name,
        'token_expires_at': connection.token_expires_at,
    }, status=status.HTTP_200_OK)
