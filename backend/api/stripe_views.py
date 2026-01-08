"""
Stripe webhook and subscription management views
"""
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from . import stripe_service
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return HttpResponse(status=400)

    # Handle the event
    event_type = event['type']
    logger.info(f"Received Stripe webhook: {event_type}")

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        stripe_service.handle_checkout_completed(session)

    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        stripe_service.handle_subscription_updated(subscription)

    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        stripe_service.handle_subscription_deleted(subscription)

    return HttpResponse(status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """Create a Stripe Checkout session for the user"""
    try:
        # Get success and cancel URLs from request
        success_url = request.data.get('success_url', f"{settings.FRONTEND_URL}/subscription/success")
        cancel_url = request.data.get('cancel_url', f"{settings.FRONTEND_URL}/subscription/cancel")

        session = stripe_service.create_checkout_session(
            user=request.user,
            success_url=success_url,
            cancel_url=cancel_url
        )

        return Response({
            'sessionId': session.id,
            'url': session.url
        })
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_portal_session(request):
    """Create a Stripe Customer Portal session for subscription management"""
    try:
        return_url = request.data.get('return_url', f"{settings.FRONTEND_URL}/profile")

        session = stripe_service.create_customer_portal_session(
            user=request.user,
            return_url=return_url
        )

        return Response({
            'url': session.url
        })
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """Get current user's subscription status"""
    try:
        profile = request.user.profile
        subscription = request.user.subscriptions.filter(
            status__in=['active', 'trialing']
        ).first()

        return Response({
            'has_subscription': subscription is not None,
            'subscription_status': subscription.status if subscription else None,
            'trial_ends_at': profile.trial_ends_at,
            'is_trial_active': profile.is_trial_active(),
            'can_use_service': profile.can_use_service(),
            'current_period_end': subscription.current_period_end if subscription else None,
        })
    except Exception as e:
        logger.error(f"Error fetching subscription status: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
