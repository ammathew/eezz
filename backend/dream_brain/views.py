"""
Dream Brain API views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import DailyInsight, TimelineEvent


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dream_brain_data(request):
    """
    Get user's complete Dream Brain data:
    - Daily insights sent
    - Timeline events
    """
    user = request.user

    # Get daily insights
    daily_insights = DailyInsight.objects.filter(
        user=user,
        status='sent'
    ).order_by('-created_at')[:20]

    insights_data = []
    for insight in daily_insights:
        # Find responses to this insight
        responses = insight.responses.all()

        insights_data.append({
            'id': str(insight.insight_id),
            'subject': insight.subject,
            'content': insight.content,
            'sent_at': insight.sent_at.isoformat() if insight.sent_at else None,
            'responses': [{
                'id': str(resp.response_id),
                'content': resp.cleaned_content or resp.raw_content,
                'received_at': resp.received_at.isoformat(),
            } for resp in responses]
        })

    # Get timeline events
    timeline_events = TimelineEvent.objects.filter(
        user=user
    ).order_by('-at')[:100]

    timeline_data = [{
        'id': str(event.event_id),
        'kind': event.get_kind_display(),
        'at': event.at.isoformat(),
        'data': event.data,
        'dream_id': str(event.dream.id) if event.dream else None,
    } for event in timeline_events]

    return Response({
        'daily_insights': insights_data,
        'timeline': timeline_data,
    }, status=status.HTTP_200_OK)
