from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Conversation, Message, DreamSymbol, UserProfile
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    ConversationCalendarSerializer,
    MessageSerializer
)
from .gemini_service import GeminiService
from dream_brain.services.timeline_service import TimelineService


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'ok',
        'message': 'Django backend is running!'
    }, status=status.HTTP_200_OK)


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversations"""
    serializer_class = ConversationSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer

    def get_queryset(self):
        """Filter conversations by the current user"""
        if self.request.user.is_authenticated:
            return Conversation.objects.filter(user=self.request.user).prefetch_related('messages')
        return Conversation.objects.none()

    def perform_create(self, serializer):
        """Set the user when creating a conversation"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """
        Get conversations grouped by date for calendar view

        Query parameters:
        - start_date: YYYY-MM-DD (optional, defaults to first day of current month)
        - end_date: YYYY-MM-DD (optional, defaults to last day of current month)
        """
        from datetime import datetime, timedelta
        from django.utils import timezone

        # Parse date parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        # Default to current month if not provided
        now = timezone.now()
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = now.replace(day=1).date()

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Last day of month
            next_month = now.replace(day=28) + timedelta(days=4)
            end_date = (next_month - timedelta(days=next_month.day)).date()

        # Query conversations in date range with prefetched messages
        conversations = self.get_queryset().filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).prefetch_related('messages').order_by('created_at')

        # Group by date
        from collections import defaultdict
        dreams_by_date = defaultdict(list)

        for conv in conversations:
            date_key = conv.created_at.date().isoformat()
            dreams_by_date[date_key].append(
                ConversationCalendarSerializer(conv).data
            )

        return Response(dict(dreams_by_date))

    def _is_dream_interpretation_request(self, message):
        """Check if message is about dream interpretation"""
        dream_keywords = [
            'dream', 'dreamed', 'dreamt', 'nightmare',
            'i had a dream', 'i dreamed', 'i dreamt'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in dream_keywords)

    def _get_dream_symbols(self, keywords):
        """Query database for dream symbols matching keywords"""
        from .dream_utils import get_dream_symbols
        return get_dream_symbols(keywords)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a message in a conversation and get a response from Gemini

        Expected payload:
        {
            "content": "User message content"
        }
        """
        conversation = self.get_object()
        user_message_content = request.data.get('content', '').strip()

        if not user_message_content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create user message
            user_message = Message.objects.create(
                conversation=conversation,
                role='user',
                content=user_message_content
            )

            # Update conversation title with first user message if it's still the default
            # Check if this is the first user message (count only user role messages)
            user_message_count = conversation.messages.filter(role='user').count()

            if conversation.title == "New Conversation" and user_message_count == 1:
                # Set title to first 50 characters of the first user message
                title = user_message_content[:50]
                if len(user_message_content) > 50:
                    title += "..."
                conversation.title = title
                conversation.save()

                # Note: Timeline events (dream and chat summary) are now created by
                # the scheduled task 'process_stale_conversations' which runs periodically
                # to process conversations after they've been idle for a period of time.

            # Prepare conversation history for Gemini
            messages = list(conversation.messages.values('role', 'content'))

            # Initialize Gemini service
            gemini_service = GeminiService()

            # Always extract dream keywords and symbols (since we're a dream interpreter)
            dream_symbols = None
            # Extract keywords using LLM
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[CHAT VIEW] Extracting keywords from: {user_message_content[:100]}...")

            keywords = gemini_service.extract_dream_keywords(user_message_content)
            logger.info(f"[CHAT VIEW] Extracted keywords: {keywords}")

            # Query database for dream symbols
            if keywords:
                dream_symbols = self._get_dream_symbols(keywords)
                logger.info(f"[CHAT VIEW] Found dream symbols: {list(dream_symbols.keys()) if dream_symbols else 'None'}")
            else:
                logger.warning(f"[CHAT VIEW] No keywords extracted, skipping symbol lookup")

            # Get response from Gemini with dream symbols if available
            ai_response = gemini_service.generate_response(messages, dream_symbols=dream_symbols)

            # Create assistant message
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response
            )

            # Note: Chat summary timeline events are now created by the scheduled task
            # 'process_stale_conversations' which runs periodically to process
            # conversations after they've been idle for a period of time.

            # Refresh conversation from database to get updated title
            conversation.refresh_from_db()

            # Return both messages and updated conversation info
            return Response({
                'user_message': MessageSerializer(user_message).data,
                'assistant_message': MessageSerializer(assistant_message).data,
                'conversation': {
                    'id': conversation.id,
                    'title': conversation.title,
                    'updated_at': conversation.updated_at
                }
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to generate response: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing messages"""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        """Optionally filter messages by conversation"""
        queryset = Message.objects.all()
        conversation_id = self.request.query_params.get('conversation', None)
        if conversation_id is not None:
            queryset = queryset.filter(conversation_id=conversation_id)
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_preferences(request):
    """
    Get user's email frequency preferences
    """
    try:
        profile = request.user.profile
        return Response({
            'email_frequency': profile.email_frequency,
            'choices': UserProfile.EMAIL_FREQUENCY_CHOICES
        }, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
        return Response({
            'email_frequency': profile.email_frequency,
            'choices': UserProfile.EMAIL_FREQUENCY_CHOICES
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_email_preferences(request):
    """
    Update user's email frequency preferences

    Expected payload:
    {
        "email_frequency": "daily" | "every_2_days" | "every_3_days" | "every_5_days" | "weekly" | "off"
    }
    """
    email_frequency = request.data.get('email_frequency')

    if not email_frequency:
        return Response(
            {'error': 'email_frequency is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate choice
    valid_choices = [choice[0] for choice in UserProfile.EMAIL_FREQUENCY_CHOICES]
    if email_frequency not in valid_choices:
        return Response(
            {'error': f'Invalid email_frequency. Must be one of: {", ".join(valid_choices)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)

    profile.email_frequency = email_frequency
    profile.save()

    return Response({
        'message': 'Email preferences updated successfully',
        'email_frequency': profile.email_frequency
    }, status=status.HTTP_200_OK)
