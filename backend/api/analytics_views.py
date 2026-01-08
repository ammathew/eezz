from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Count, Q, F, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile, PublicDreamSubmission, Subscription
from emails.models import Email, EmailEvent
from dream_brain.models import DailyInsight, DailyInsightResponse


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_overview(request):
    """
    Get overview analytics for marketing dashboard
    Requires superuser permission
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Admin access required'},
            status=403
        )

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # User counts
    total_users = User.objects.count()
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_users_7d = User.objects.filter(date_joined__gte=seven_days_ago).count()

    # Active users (logged in recently)
    active_users_30d = User.objects.filter(last_login__gte=thirty_days_ago).count()
    active_users_7d = User.objects.filter(last_login__gte=seven_days_ago).count()

    # Subscription stats
    total_subscriptions = Subscription.objects.filter(status='active').count()
    trial_users = Subscription.objects.filter(status='trialing').count()
    canceled_subscriptions = Subscription.objects.filter(status='canceled').count()

    # Public dream funnel
    total_public_dreams = PublicDreamSubmission.objects.count()
    public_with_email = PublicDreamSubmission.objects.filter(email__isnull=False).exclude(email='').count()
    public_sent = PublicDreamSubmission.objects.filter(status='sent').count()

    # Email stats (last 30 days)
    emails_sent_30d = Email.objects.filter(created_at__gte=thirty_days_ago).count()

    # Email opens (unique)
    email_opens_30d = EmailEvent.objects.filter(
        event_type='open',
        created_at__gte=thirty_days_ago
    ).values('email').distinct().count()

    # Email clicks
    email_clicks_30d = EmailEvent.objects.filter(
        event_type='click',
        created_at__gte=thirty_days_ago
    ).count()

    # Daily insights stats
    daily_insights_sent_30d = DailyInsight.objects.filter(
        sent_at__gte=thirty_days_ago
    ).count()

    daily_insights_opened = EmailEvent.objects.filter(
        event_type='open',
        email__email_type='appuser-followup',
        created_at__gte=thirty_days_ago
    ).values('email').distinct().count()

    # Calculate rates
    email_open_rate = (email_opens_30d / emails_sent_30d * 100) if emails_sent_30d > 0 else 0
    email_click_rate = (email_clicks_30d / emails_sent_30d * 100) if emails_sent_30d > 0 else 0
    public_conversion_rate = (public_with_email / total_public_dreams * 100) if total_public_dreams > 0 else 0

    return Response({
        'overview': {
            'total_users': total_users,
            'new_users_30d': new_users_30d,
            'new_users_7d': new_users_7d,
            'active_users_30d': active_users_30d,
            'active_users_7d': active_users_7d,
        },
        'subscriptions': {
            'active': total_subscriptions,
            'trial': trial_users,
            'canceled': canceled_subscriptions,
        },
        'public_funnel': {
            'total_submissions': total_public_dreams,
            'email_captured': public_with_email,
            'interpretations_sent': public_sent,
            'conversion_rate': round(public_conversion_rate, 2),
        },
        'email_performance': {
            'emails_sent_30d': emails_sent_30d,
            'unique_opens_30d': email_opens_30d,
            'clicks_30d': email_clicks_30d,
            'open_rate': round(email_open_rate, 2),
            'click_rate': round(email_click_rate, 2),
        },
        'daily_insights': {
            'sent_30d': daily_insights_sent_30d,
            'opened_30d': daily_insights_opened,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_signups_over_time(request):
    """
    Get user signups over time (daily for last 30 days)
    Requires superuser permission
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Admin access required'},
            status=403
        )

    # Get period from query params (default 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    signups = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        date=TruncDate('date_joined')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    return Response({
        'signups': list(signups)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_email_engagement(request):
    """
    Get email engagement metrics over time
    Requires superuser permission
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Admin access required'},
            status=403
        )

    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Emails sent per day
    emails_by_day = Email.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Opens per day
    opens_by_day = EmailEvent.objects.filter(
        event_type='open',
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('email', distinct=True)
    ).order_by('date')

    # Clicks per day
    clicks_by_day = EmailEvent.objects.filter(
        event_type='click',
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    return Response({
        'emails_sent': list(emails_by_day),
        'opens': list(opens_by_day),
        'clicks': list(clicks_by_day),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_public_funnel(request):
    """
    Get public dream submission funnel metrics
    Requires superuser permission
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Admin access required'},
            status=403
        )

    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Get daily funnel metrics
    submissions_by_day = PublicDreamSubmission.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Count('id'),
        with_email=Count('id', filter=Q(email__isnull=False) & ~Q(email='')),
        sent=Count('id', filter=Q(status='sent'))
    ).order_by('date')

    return Response({
        'funnel_by_day': list(submissions_by_day)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_user_retention(request):
    """
    Get user retention/activity metrics
    Requires superuser permission
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Admin access required'},
            status=403
        )

    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Daily active users (users who logged in)
    daily_active = User.objects.filter(
        last_login__gte=start_date
    ).annotate(
        date=TruncDate('last_login')
    ).values('date').annotate(
        count=Count('id', distinct=True)
    ).order_by('date')

    return Response({
        'daily_active_users': list(daily_active)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_top_users(request):
    """
    Get top engaged users by various metrics
    Requires superuser permission
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Admin access required'},
            status=403
        )

    limit = int(request.GET.get('limit', 10))

    # Users with most conversations
    from .models import Conversation
    top_by_conversations = User.objects.annotate(
        conversation_count=Count('conversations')
    ).filter(
        conversation_count__gt=0
    ).order_by('-conversation_count')[:limit].values(
        'id', 'email', 'first_name', 'last_name', 'conversation_count'
    )

    # Users with most messages
    from .models import Message
    top_by_messages = User.objects.annotate(
        message_count=Count('conversations__messages')
    ).filter(
        message_count__gt=0
    ).order_by('-message_count')[:limit].values(
        'id', 'email', 'first_name', 'last_name', 'message_count'
    )

    return Response({
        'top_by_conversations': list(top_by_conversations),
        'top_by_messages': list(top_by_messages),
    })
