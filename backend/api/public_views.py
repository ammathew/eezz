from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
import logging
import threading

from .models import PublicDreamSubmission
from .serializers import PublicDreamSubmissionSerializer, EmailCaptureSerializer
from .gemini_service import GeminiService
from .email_service import EmailService

logger = logging.getLogger(__name__)


def process_dream_interpretation_async(submission_id):
    """
    Background task to generate interpretation and send email
    Runs in a separate thread to avoid blocking the HTTP response
    """
    try:
        submission = PublicDreamSubmission.objects.get(submission_id=submission_id)

        logger.info(f"Starting background interpretation for {submission_id}")

        # Generate interpretation using Gemini
        gemini_service = GeminiService()

        # Extract keywords from the dream
        keywords = gemini_service.extract_dream_keywords(submission.dream_text)
        logger.info(f"Extracted keywords for {submission_id}: {keywords}")

        # Get dream symbols from database using shared utility
        from .dream_utils import get_dream_symbols
        dream_symbols = get_dream_symbols(keywords)
        if dream_symbols:
            logger.info(f"Found {len(dream_symbols)} symbols for {submission_id}: {list(dream_symbols.keys())}")
        else:
            logger.info(f"No symbols found in database for {submission_id}")

        # Create messages in the same format as authenticated chat
        messages = [{
            'role': 'user',
            'content': submission.dream_text
        }]

        logger.info(f"[PUBLIC INTERPRETATION] Calling generate_response for {submission_id}")
        logger.info(f"[PUBLIC INTERPRETATION] Dream text: {submission.dream_text}")
        logger.info(f"[PUBLIC INTERPRETATION] Symbols being passed: {list(dream_symbols.keys()) if dream_symbols else 'None'}")

        interpretation = gemini_service.generate_response(
            messages=messages,
            dream_symbols=dream_symbols
        )

        if not interpretation:
            raise Exception("Failed to generate interpretation")

        submission.interpretation = interpretation
        submission.save()

        logger.info(f"Interpretation generated for submission {submission_id}")

        # Send email with interpretation
        email_sent = EmailService.send_dream_interpretation(submission)

        if email_sent:
            logger.info(f"Successfully sent interpretation email for {submission_id}")
        else:
            logger.error(f"Failed to send email for submission {submission_id}")

    except Exception as e:
        logger.error(f"Failed to process dream interpretation for {submission_id}: {str(e)}")
        try:
            submission = PublicDreamSubmission.objects.get(submission_id=submission_id)
            submission.status = 'failed'
            submission.save()
        except Exception as save_error:
            logger.error(f"Failed to update status for {submission_id}: {str(save_error)}")


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_dream(request):
    """
    Public endpoint for submitting a dream for interpretation

    POST /api/public/submit-dream/
    Body: {
        "dream_text": "I dreamed about flying over mountains..."
    }

    Returns: {
        "submission_id": "uuid",
        "dream_text": "...",
        "status": "pending",
        "created_at": "timestamp"
    }
    """
    serializer = PublicDreamSubmissionSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Validate dream text length
    dream_text = serializer.validated_data.get('dream_text', '')
    if len(dream_text.strip()) < 2:
        return Response(
            {'error': 'Dream description must be at least 2 characters long.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(dream_text) > 5000:
        return Response(
            {'error': 'Dream description is too long. Please keep it under 5000 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create submission
    submission = serializer.save()

    logger.info(f"New public dream submission created: {submission.submission_id}")

    return Response(
        PublicDreamSubmissionSerializer(submission).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_email(request):
    """
    Public endpoint for capturing email and sending interpretation

    POST /api/public/submit-email/
    Body: {
        "submission_id": "uuid",
        "email": "user@example.com"
    }

    Returns: {
        "success": true,
        "message": "Check your email for your dream interpretation!"
    }
    """
    serializer = EmailCaptureSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    submission_id = serializer.validated_data['submission_id']
    email = serializer.validated_data['email']

    # Find submission
    try:
        submission = PublicDreamSubmission.objects.get(submission_id=submission_id)
    except PublicDreamSubmission.DoesNotExist:
        return Response(
            {'error': 'Dream submission not found. Please submit your dream again.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if email already submitted
    if submission.email and submission.status == 'sent':
        return Response(
            {'error': 'This dream has already been interpreted and sent. Please check your email.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update submission with email
    submission.email = email
    submission.status = 'processing'
    submission.save()

    logger.info(f"Email captured for submission {submission_id}: {email}")

    # Start background thread to process interpretation and send email
    # This allows us to return immediately without waiting for Gemini API
    thread = threading.Thread(
        target=process_dream_interpretation_async,
        args=(submission_id,),
        daemon=True
    )
    thread.start()

    logger.info(f"Started background processing for submission {submission_id}")

    # Return success immediately - email will be sent when processing completes
    return Response({
        'success': True,
        'message': 'Your interpretation is being generated and will be emailed to you shortly!'
    }, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def unsubscribe(request, token):
    """
    Public endpoint for unsubscribing from follow-up emails

    GET /api/public/unsubscribe/<token>/
    Returns unsubscribe confirmation page data

    POST /api/public/unsubscribe/<token>/
    Processes the unsubscribe request

    Returns: {
        "success": true,
        "message": "You have been unsubscribed from follow-up emails."
    }
    """
    try:
        submission = PublicDreamSubmission.objects.get(unsubscribe_token=token)
    except PublicDreamSubmission.DoesNotExist:
        return Response(
            {'error': 'Invalid unsubscribe link. This link may be expired or incorrect.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        # Return current subscription status
        return Response({
            'email': submission.email,
            'is_subscribed': submission.email_subscribed,
            'submission_id': str(submission.submission_id)
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Unsubscribe the user from ALL submissions with this email
        email = submission.email

        # Check if already unsubscribed
        if not submission.email_subscribed:
            return Response(
                {'success': True, 'message': 'You are already unsubscribed from follow-up emails.'},
                status=status.HTTP_200_OK
            )

        # Update ALL submissions with this email address
        updated_count = PublicDreamSubmission.objects.filter(
            email=email
        ).update(email_subscribed=False)

        logger.info(f"User {email} unsubscribed from follow-up emails ({updated_count} submission(s) updated)")

        return Response({
            'success': True,
            'message': 'You have been successfully unsubscribed from follow-up emails. You will no longer receive dream insights from us.'
        }, status=status.HTTP_200_OK)
