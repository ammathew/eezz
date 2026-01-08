"""
Stripe subscription management service
"""
import stripe
from django.conf import settings
from django.utils import timezone
from .models import Subscription, UserProfile

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_customer(user):
    """Create a Stripe customer for the user"""
    customer = stripe.Customer.create(
        email=user.email,
        name=f"{user.first_name} {user.last_name}".strip() or user.email,
        metadata={
            'user_id': user.id,
            'username': user.username
        }
    )
    return customer.id


def create_checkout_session(user, success_url, cancel_url):
    """Create a Stripe Checkout session for subscription"""
    # Get or create Stripe customer (but don't create subscription record yet)
    try:
        subscription = Subscription.objects.filter(user=user).first()
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            customer_id = create_customer(user)
    except Exception as e:
        customer_id = create_customer(user)

    # Create checkout session
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': settings.STRIPE_PRICE_ID,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'user_id': user.id,
        }
    )

    return session


def create_customer_portal_session(user, return_url):
    """Create a Stripe Customer Portal session for subscription management"""
    try:
        subscription = Subscription.objects.get(user=user)
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url,
        )
        return session
    except Subscription.DoesNotExist:
        raise ValueError("User does not have a subscription")


def handle_checkout_completed(session):
    """Handle successful checkout completion"""
    user_id = session.metadata.get('user_id')
    customer_id = session.customer
    subscription_id = session.subscription

    # Get the subscription details from Stripe
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)

    # Update or create subscription record
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)

    # Safely get period timestamps
    current_period_start = None
    current_period_end = None
    if hasattr(stripe_subscription, 'current_period_start'):
        current_period_start = timezone.datetime.fromtimestamp(
            stripe_subscription.current_period_start,
            tz=timezone.get_current_timezone()
        )
    if hasattr(stripe_subscription, 'current_period_end'):
        current_period_end = timezone.datetime.fromtimestamp(
            stripe_subscription.current_period_end,
            tz=timezone.get_current_timezone()
        )

    subscription, _ = Subscription.objects.update_or_create(
        stripe_customer_id=customer_id,
        defaults={
            'user': user,
            'stripe_subscription_id': subscription_id,
            'status': stripe_subscription.status,
            'current_period_start': current_period_start,
            'current_period_end': current_period_end,
            'cancel_at_period_end': getattr(stripe_subscription, 'cancel_at_period_end', False),
        }
    )

    return subscription


def handle_subscription_updated(stripe_subscription):
    """Handle subscription update webhook"""
    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_subscription.id
        )
        subscription.status = stripe_subscription.status

        # Safely update period timestamps
        if hasattr(stripe_subscription, 'current_period_start'):
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_start,
                tz=timezone.get_current_timezone()
            )
        if hasattr(stripe_subscription, 'current_period_end'):
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end,
                tz=timezone.get_current_timezone()
            )

        subscription.cancel_at_period_end = getattr(stripe_subscription, 'cancel_at_period_end', False)
        subscription.save()
        return subscription
    except Subscription.DoesNotExist:
        # Subscription doesn't exist in our database yet
        return None


def handle_subscription_deleted(stripe_subscription):
    """Handle subscription cancellation webhook"""
    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_subscription.id
        )
        subscription.status = 'canceled'
        subscription.save()
        return subscription
    except Subscription.DoesNotExist:
        return None
