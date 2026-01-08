"""
Email webhook views.
Handles incoming webhooks from email providers (Postmark).
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import logging

from .models import Email, EmailEvent, InboundEmail
from dream_brain.services.timeline_service import TimelineService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def postmark_inbound_webhook(request):
    """
    Handle inbound email webhook from Postmark.

    Postmark sends inbound emails to this endpoint.
    We parse them and create ReflectionResponse records.

    Postmark Inbound Webhook Format:
    https://postmarkapp.com/developer/webhooks/inbound-webhook
    """
    try:
        # Parse JSON payload
        data = json.loads(request.body)

        logger.info(f"Received inbound webhook from Postmark")
        logger.info(f"Payload keys: {list(data.keys())}")

        # Extract key fields (handle both test and real webhooks)
        from_email = data.get('From', data.get('FromFull', {}).get('Email', ''))
        from_name = data.get('FromName', '')
        to_email = data.get('To', data.get('ToFull', [{}])[0].get('Email', ''))
        subject = data.get('Subject', '')
        text_body = data.get('TextBody', '')
        html_body = data.get('HtmlBody', '')
        message_id = data.get('MessageID', '')

        logger.info(f"Parsed - From: {from_email}, To: {to_email}, Subject: {subject}")

        # Validate required fields
        if not to_email:
            logger.error("Missing 'To' email in webhook payload")
            return JsonResponse({'error': 'Missing To email'}, status=400)

        # Create InboundEmail record (using correct field names from model)
        inbound_email = InboundEmail.objects.create(
            sender_email=from_email or 'test@test.com',
            sender_name=from_name,
            recipient_email=to_email,
            subject=subject,
            text_content=text_body,
            html_content=html_body,
            raw_data=data
        )

        logger.info(f"Created InboundEmail {inbound_email.id}")

        # Check if this is a daily insight reply
        # Reply-to format: {hash}+daily-{uuid}@inbound.postmarkapp.com
        if 'daily-' in to_email and '@inbound.postmarkapp.com' in to_email:
            process_daily_insight_reply(inbound_email, to_email)

        # Return success (HTTP 200)
        return JsonResponse({'status': 'success'}, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    except Exception as e:
        logger.error(f"Error processing inbound webhook: {type(e).__name__}: {str(e)}")
        return JsonResponse({'error': 'Internal error'}, status=500)


@csrf_exempt
@require_POST
def postmark_event_webhook(request):
    """
    Handle email event webhooks from Postmark (opens, clicks, bounces, etc).

    Postmark Event Webhook Format:
    https://postmarkapp.com/developer/webhooks/webhooks-overview
    """
    try:
        # Parse JSON payload
        data = json.loads(request.body)

        record_type = data.get('RecordType')  # e.g., 'Open', 'Click', 'Bounce', 'Delivery'
        message_id = data.get('MessageID')

        logger.info(f"Received {record_type} event for message {message_id}")

        # Find the email by provider_message_id
        email = Email.objects.filter(provider_message_id=message_id).first()

        if not email:
            logger.warning(f"No email found for message_id: {message_id}")
            return JsonResponse({'status': 'warning', 'message': 'Email not found'}, status=200)

        # Map Postmark event types to our event types
        event_type_map = {
            'Delivery': 'delivered',
            'Bounce': 'bounced',
            'Open': 'opened',
            'Click': 'clicked',
            'SpamComplaint': 'spam_complaint',
        }

        event_type = event_type_map.get(record_type, 'other')

        # Create EmailEvent
        event = EmailEvent.objects.create(
            email=email,
            event_type=event_type,
            raw_data=data,
            user_agent=data.get('UserAgent'),
            ip_address=data.get('Geo', {}).get('IP')
        )

        logger.info(f"Created EmailEvent {event.id} ({event_type}) for email {email.email_id}")

        return JsonResponse({'status': 'success'}, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    except Exception as e:
        logger.error(f"Error processing event webhook: {type(e).__name__}: {str(e)}")
        return JsonResponse({'error': 'Internal error'}, status=500)


def clean_email_reply(text_content):
    """
    Clean email reply content to extract only the user's actual response.
    Removes quoted text, signatures, and email footers.

    Args:
        text_content: Raw email text content

    Returns:
        Cleaned user response text
    """
    if not text_content:
        return ""

    lines = text_content.split('\n')
    cleaned_lines = []

    # Common patterns that indicate quoted/forwarded content
    quote_markers = [
        'On ',  # "On Thu, Jan 1, 2026 at 5:26PM"
        '> ',   # Email quote markers
        '>>',   # Multiple level quotes
        '___',  # Signature separators
        '--',   # Signature separators
        'From:',
        'Sent:',
        'To:',
        'Subject:',
        'wrote:',
        'This email was sent by',
        'Visit Unravel',
        'https://',
        'Your personal dream interpretation',
        '*Unravel*',
        'Unravel <hello@',
    ]

    for line in lines:
        line_stripped = line.strip()

        # Stop at first quote marker
        if any(line.startswith(marker) or line_stripped.startswith(marker) for marker in quote_markers):
            break

        # Skip empty lines at the start
        if not cleaned_lines and not line_stripped:
            continue

        cleaned_lines.append(line)

    # Join and clean up
    cleaned = '\n'.join(cleaned_lines).strip()

    # Remove trailing empty lines
    while cleaned.endswith('\n\n'):
        cleaned = cleaned.rstrip('\n')

    return cleaned


def process_daily_insight_reply(inbound_email, to_email):
    """
    Process a reply to a daily insight email.
    Creates a DailyInsightResponse and timeline event.

    Args:
        inbound_email: InboundEmail object
        to_email: The reply-to address (e.g., {hash}+daily-{uuid}@inbound.postmarkapp.com)
    """
    try:
        from dream_brain.models import DailyInsight, DailyInsightResponse

        # Find the daily insight by reply_to_email
        daily_insight = DailyInsight.objects.filter(reply_to_email=to_email).first()

        if not daily_insight:
            logger.warning(f"No daily insight found for reply-to: {to_email}")
            return

        logger.info(f"Found daily insight {daily_insight.insight_id} for reply")

        # Clean the email reply to extract only user's response
        cleaned_content = clean_email_reply(inbound_email.text_content)

        logger.info(f"Cleaned email reply: {len(inbound_email.text_content)} -> {len(cleaned_content)} chars")

        # Create DailyInsightResponse
        response = DailyInsightResponse.objects.create(
            daily_insight=daily_insight,
            user=daily_insight.user,
            raw_content=inbound_email.text_content,
            cleaned_content=cleaned_content
        )

        logger.info(f"Created DailyInsightResponse {response.response_id} for daily insight")

        # Mark inbound email as processed
        inbound_email.processed = True
        inbound_email.save()

        # Get user's most recent dream for timeline context
        last_dream = daily_insight.user.conversations.order_by('-created_at').first()

        # Create timeline event for email response
        TimelineService.create_email_response_summary_event(
            user=daily_insight.user,
            response_content=cleaned_content,
            dream=last_dream,  # Link to the dream if available
            source_type='daily_insight'
        )

        logger.info(f"Created timeline event for daily insight response")

        # Mark response as processed
        response.processed = True
        response.processed_at = timezone.now()
        response.save()

    except Exception as e:
        logger.error(f"Error processing daily insight reply: {type(e).__name__}: {str(e)}")
