import base64
import json
import logging
from datetime import datetime, timedelta

import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .ad_renderer import render_ad_image
from .gemini_service import GeminiService
from .models import FacebookConnection
from .dev_auth import resolve_request_user

logger = logging.getLogger(__name__)
FB_API_VERSION = 'v19.0'


def _image_to_data_url(image_bytes):
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _get_account_id(raw_id):
    if not raw_id:
        return ''
    return raw_id if raw_id.startswith('act_') else f"act_{raw_id}"


def _graph_url(path):
    return f"https://graph.facebook.com/{FB_API_VERSION}/{path.lstrip('/')}"


def _ensure_facebook_connection(user):
    connection = getattr(user, 'facebook_connection', None)
    if not connection or not connection.access_token:
        raise ValueError('Facebook not connected')
    if not connection.page_id:
        raise ValueError('Facebook Page not selected')
    if not connection.ad_account_id:
        raise ValueError('Facebook Ad Account not selected')
    return connection


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_ad(request):
    user = resolve_request_user(request)
    if not user:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    product = str(request.data.get('product', '')).strip()
    audience = str(request.data.get('audience', '')).strip()
    offer = str(request.data.get('offer', '')).strip()
    proof = str(request.data.get('proof', '')).strip()
    tone = str(request.data.get('tone', '')).strip()
    cta = str(request.data.get('cta', '')).strip()
    image_text_override = str(request.data.get('image_text', '')).strip()

    if not product or not audience:
        return Response(
            {'error': 'product and audience are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    gemini = GeminiService()
    ad_copy = gemini.generate_ad_copy({
        'product': product,
        'audience': audience,
        'offer': offer,
        'proof': proof,
        'tone': tone,
        'cta': cta,
    })

    if image_text_override:
        ad_copy['image_text'] = image_text_override

    fallback_text = ad_copy.get('headline') or product
    image_text = ad_copy.get('image_text') or fallback_text
    image_bytes = render_ad_image(image_text)

    return Response({
        'primary_text': ad_copy.get('primary_text', ''),
        'headline': ad_copy.get('headline', ''),
        'cta': ad_copy.get('cta', ''),
        'image_text': image_text,
        'image_data_url': _image_to_data_url(image_bytes),
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def post_to_facebook(request):
    user = resolve_request_user(request)
    if not user:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    message = str(request.data.get('primary_text', '')).strip()
    image_text = str(request.data.get('image_text', '')).strip()

    if not message or not image_text:
        return Response(
            {'error': 'primary_text and image_text are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    connection = getattr(user, 'facebook_connection', None)
    if not connection or not connection.page_id or not connection.page_access_token:
        return Response(
            {'error': 'Facebook not connected or missing page access token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    image_bytes = render_ad_image(image_text)
    url = f"https://graph.facebook.com/{FB_API_VERSION}/{connection.page_id}/photos"
    files = {
        'source': ('ad.png', image_bytes, 'image/png'),
    }
    payload = {
        'message': message,
        'access_token': connection.page_access_token,
        'published': 'true',
    }

    try:
        response = requests.post(url, data=payload, files=files, timeout=30)
    except requests.RequestException as exc:
        logger.error("Facebook post failed", exc_info=True)
        return Response(
            {'error': f'Failed to post to Facebook: {str(exc)}'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    if not response.ok:
        logger.error("Facebook API error: %s", response.text)
        return Response(
            {'error': 'Facebook API error', 'details': response.json()},
            status=status.HTTP_502_BAD_GATEWAY
        )

    return Response(response.json(), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def launch_facebook_ad(request):
    """
    Create campaign, ad set, creative, and ad in the user's ad account.
    """
    user = resolve_request_user(request)
    if not user:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    try:
        connection = _ensure_facebook_connection(user)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    destination_url = str(request.data.get('destination_url', '')).strip()
    daily_budget = request.data.get('daily_budget', '')
    headline = str(request.data.get('headline', '')).strip()
    primary_text = str(request.data.get('primary_text', '')).strip()
    image_text = str(request.data.get('image_text', '')).strip()
    cta_raw = str(request.data.get('cta', '')).strip()
    campaign_name = str(request.data.get('campaign_name', '')).strip() or 'Ad Studio Campaign'
    adset_name = str(request.data.get('adset_name', '')).strip() or 'Ad Studio Ad Set'
    ad_name = str(request.data.get('ad_name', '')).strip() or 'Ad Studio Ad'
    status_value = str(request.data.get('status', '')).strip().upper() or 'PAUSED'
    countries = request.data.get('countries') or ['US']
    age_min = int(request.data.get('age_min', 18))
    age_max = int(request.data.get('age_max', 65))

    if not destination_url or not primary_text or not image_text:
        return Response(
            {'error': 'destination_url, primary_text, and image_text are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        daily_budget = int(float(daily_budget) * 100)
    except (TypeError, ValueError):
        return Response(
            {'error': 'daily_budget must be a number (USD)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cta_map = {
        'Learn More': 'LEARN_MORE',
        'Get Demo': 'GET_OFFER',
        'Start Free': 'START_TRIAL',
        'Sign Up': 'SIGN_UP',
        'Book Call': 'CONTACT_US',
        'Download': 'DOWNLOAD',
    }
    cta = cta_map.get(cta_raw, cta_raw.upper() if cta_raw else 'LEARN_MORE')

    account_id = _get_account_id(connection.ad_account_id)
    access_token = connection.access_token

    try:
        image_bytes = render_ad_image(image_text)
        image_response = requests.post(
            _graph_url(f"{account_id}/adimages"),
            files={'source': ('ad.png', image_bytes, 'image/png')},
            data={'access_token': access_token},
            timeout=30
        )
        image_response.raise_for_status()
        images_payload = image_response.json().get('images', {})
        if not images_payload:
            raise ValueError('No image hash returned')
        image_hash = next(iter(images_payload.values())).get('hash')
        if not image_hash:
            raise ValueError('Invalid image hash response')

        campaign_response = requests.post(
            _graph_url(f"{account_id}/campaigns"),
            data={
                'access_token': access_token,
                'name': campaign_name,
                'objective': 'OUTCOME_TRAFFIC',
                'status': status_value,
                'special_ad_categories': json.dumps([]),
                'is_adset_budget_sharing_enabled': 'false',
            },
            timeout=30
        )
        campaign_response.raise_for_status()
        campaign_id = campaign_response.json().get('id')

        adset_response = requests.post(
            _graph_url(f"{account_id}/adsets"),
            data={
                'access_token': access_token,
                'name': adset_name,
                'campaign_id': campaign_id,
                'daily_budget': daily_budget,
                'billing_event': 'IMPRESSIONS',
                'optimization_goal': 'LINK_CLICKS',
                'bid_strategy': 'LOWEST_COST_WITHOUT_CAP',
                'status': status_value,
                'start_time': f"{(datetime.utcnow() + timedelta(minutes=5)).isoformat()}Z",
                'targeting': json.dumps({
                    'geo_locations': {'countries': countries},
                    'age_min': age_min,
                    'age_max': age_max,
                }),
                'promoted_object': json.dumps({
                    'page_id': connection.page_id,
                }),
            },
            timeout=30
        )
        adset_response.raise_for_status()
        adset_id = adset_response.json().get('id')

        creative_response = requests.post(
            _graph_url(f"{account_id}/adcreatives"),
            data={
                'access_token': access_token,
                'name': f"{ad_name} Creative",
                'object_story_spec': json.dumps({
                    'page_id': connection.page_id,
                    'link_data': {
                        'message': primary_text,
                        'link': destination_url,
                        'name': headline,
                        'image_hash': image_hash,
                        'call_to_action': {
                            'type': cta,
                            'value': {'link': destination_url},
                        },
                    },
                }),
            },
            timeout=30
        )
        creative_response.raise_for_status()
        creative_id = creative_response.json().get('id')

        ad_response = requests.post(
            _graph_url(f"{account_id}/ads"),
            data={
                'access_token': access_token,
                'name': ad_name,
                'adset_id': adset_id,
                'creative': json.dumps({'creative_id': creative_id}),
                'status': status_value,
            },
            timeout=30
        )
        ad_response.raise_for_status()

    except requests.RequestException as exc:
        response = getattr(exc, 'response', None)
        error_payload = None
        if response is not None:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = response.text
        logger.error(
            "Facebook marketing API error (status=%s, payload=%s)",
            getattr(response, 'status_code', None),
            error_payload,
            exc_info=True
        )
        return Response(
            {
                'error': 'Facebook marketing API error',
                'details': str(exc),
                'facebook_error': error_payload,
                'status_code': getattr(response, 'status_code', None),
            },
            status=status.HTTP_502_BAD_GATEWAY
        )
    except Exception as exc:
        logger.error("Failed to launch ad", exc_info=True)
        return Response(
            {'error': f'Failed to launch ad: {str(exc)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({
        'campaign_id': campaign_id,
        'adset_id': adset_id,
        'ad_id': ad_response.json().get('id'),
        'creative_id': creative_id,
    }, status=status.HTTP_200_OK)
