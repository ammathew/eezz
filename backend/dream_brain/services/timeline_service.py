"""
Service for creating and managing timeline events.
Timeline events are the distilled story of a user's dream journey.
"""
from django.utils import timezone
from dream_brain.models import TimelineEvent
from api.models import Conversation, Message
from api.gemini_service import GeminiService


class TimelineService:
    """Helper service for creating timeline events."""

    @staticmethod
    def create_dream_events(user, conversation):
        """
        Create 'dream' timeline events for all dreams in a conversation.
        Uses AI to intelligently parse and extract individual dreams.

        Args:
            user: User object
            conversation: Conversation object containing dreams

        Returns:
            List of TimelineEvent objects
        """
        from api.gemini_service import GeminiService
        import json
        import re

        # Get all user messages
        user_messages = conversation.messages.filter(role='user').order_by('created_at')
        if not user_messages.exists():
            return []

        # Build conversation text for AI analysis
        messages_text = ""
        for i, msg in enumerate(user_messages, 1):
            messages_text += f"Message {i} (at {msg.created_at}):\n{msg.content}\n\n"

        # Ask AI to identify dreams
        prompt = f"""Analyze this conversation and identify all distinct DREAMS the user shared.

User messages:
{messages_text}

IMPORTANT: Only identify messages that describe actual dream content (what they experienced while sleeping).
Do NOT include:
- Followup clarifications or elaborations on the same dream
- Comments about their waking life
- Questions or reactions to interpretations
- Context about their life situation

For each DISTINCT dream found, provide:
1. The message number(s) it appears in
2. A clean summary in FIRST PERSON (from the user's perspective), condensing the dream content without changing the voice

Example:
User said: "I'm sitting in front of train tracks. The engineer warns about a ball."
Summary: "I was sitting in front of train tracks when an engineer warned about a ball on the tracks."

Respond in JSON format:
{{
  "dreams": [
    {{
      "message_numbers": [1],
      "summary": "First-person summary keeping the user's voice"
    }}
  ]
}}

Keep summaries concise (1-2 sentences max).
If multiple messages describe the SAME dream with additional details, group them together.
If a message is just followup commentary (not dream content), exclude it."""

        try:
            gemini = GeminiService()
            response = gemini.generate_simple_response(prompt)

            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response)

            dreams_data = result.get('dreams', [])

            # Create timeline events for each identified dream
            events = []
            for dream_info in dreams_data:
                msg_numbers = dream_info.get('message_numbers', [])
                if not msg_numbers:
                    continue

                # Get the actual messages
                dream_messages = []
                for msg_num in msg_numbers:
                    if 1 <= msg_num <= len(user_messages):
                        dream_messages.append(list(user_messages)[msg_num - 1])

                if not dream_messages:
                    continue

                # Use the timestamp of the first message for this dream
                dream_timestamp = dream_messages[0].created_at

                # Store the summary (which contains the cleaned dream content)
                # We keep the link to conversation so we can always access full text if needed
                event = TimelineEvent.objects.create(
                    user=user,
                    dream=conversation,
                    kind='dream',
                    at=dream_timestamp,
                    data={
                        'dream_summary': dream_info.get('summary', ''),
                        'conversation_id': str(conversation.id),
                        'message_numbers': msg_numbers,
                    }
                )
                events.append(event)

            return events

        except Exception as e:
            # Fallback: create single event from first message
            first_message = user_messages.first()
            # Use first 200 chars as summary for fallback
            summary = first_message.content[:200] + ('...' if len(first_message.content) > 200 else '')
            event = TimelineEvent.objects.create(
                user=user,
                dream=conversation,
                kind='dream',
                at=conversation.created_at,
                data={
                    'dream_summary': summary,
                    'conversation_id': str(conversation.id),
                    'error': f'AI parsing failed: {str(e)}'
                }
            )
            return [event]

    @staticmethod
    def create_chat_summary_event(user, conversation):
        """
        Create a 'chat_summary' timeline event after a dream interpretation chat.

        This distills the full conversation into key takeaways.

        Args:
            user: User object
            conversation: Conversation object containing the full chat

        Returns:
            TimelineEvent object
        """
        # Get all messages in the conversation
        messages = conversation.messages.all().order_by('created_at')

        if not messages.exists():
            return None

        # Build conversation text for summarization
        chat_text = ""
        for msg in messages:
            role = "User" if msg.role == 'user' else "AI"
            chat_text += f"{role}: {msg.content}\n\n"

        # Use AI to create a concise summary
        summary_prompt = f"""Summarize this dream conversation focusing ONLY on what the user shared.

Conversation:
{chat_text}

Write a brief 1-2 sentence summary covering:
- What the user dreamed about
- Anything the user said beyond the initial dream (their thoughts, questions, reactions)

DO NOT summarize what the AI said. Only capture what the USER experienced and shared.

Keep it concise and in plain text (no JSON, no bullet points)."""

        try:
            gemini = GeminiService()
            response = gemini.generate_simple_response(summary_prompt)

            # Use the plain text response directly
            summary_data = {
                'summary': response.strip(),
            }

        except Exception as e:
            # Fallback: create a simple summary
            summary_data = {
                'summary': f"Dream interpretation conversation with {messages.count()} messages",
                'error': str(e)
            }

        event = TimelineEvent.objects.create(
            user=user,
            dream=conversation,
            kind='chat_summary',
            at=timezone.now(),
            data=summary_data
        )
        return event

    @staticmethod
    def create_email_response_summary_event(user, response_content, dream=None, source_type='daily_insight'):
        """
        Create an 'email_response_summary' timeline event when user replies to an email.

        Args:
            user: User object
            response_content: The cleaned content of the user's email reply
            dream: Optional Conversation object if response is about a specific dream
            source_type: Type of email they replied to ('daily_insight', 'reflection')

        Returns:
            TimelineEvent object
        """
        # Use AI to extract key points from the response
        summary_prompt = f"""Summarize what the user shared in their email reply about their dream.

User's response:
{response_content}

Write a brief 1-2 sentence summary of what they shared (thoughts, connections to their life, questions, reactions).

Keep it concise and in plain text (no JSON, no bullet points)."""

        try:
            gemini = GeminiService()
            response = gemini.generate_simple_response(summary_prompt)

            # Use the plain text response directly
            summary_data = {
                'summary': response.strip(),
                'source_type': source_type,
            }

        except Exception as e:
            # Fallback
            summary_data = {
                'summary': response_content[:200] + '...' if len(response_content) > 200 else response_content,
                'source_type': source_type,
                'error': str(e)
            }

        event = TimelineEvent.objects.create(
            user=user,
            dream=dream,
            kind='email_response_summary',
            at=timezone.now(),
            data=summary_data
        )
        return event

    @staticmethod
    def get_user_timeline(user, limit=20, dream=None):
        """
        Get a user's timeline events, formatted for LLM context.

        Args:
            user: User object
            limit: Maximum number of events to return
            dream: Optional Conversation object to filter by specific dream

        Returns:
            String formatted timeline for LLM prompts
        """
        query = TimelineEvent.objects.filter(user=user)
        if dream:
            query = query.filter(dream=dream)

        events = query.order_by('-at')[:limit]

        if not events.exists():
            return "No timeline events yet."

        timeline_text = "TIMELINE OF DREAM JOURNEY:\n\n"

        for event in reversed(list(events)):  # Show chronologically
            timeline_text += f"[{event.at.strftime('%Y-%m-%d')}] {event.get_kind_display()}:\n"

            if event.kind == 'dream':
                dream_summary = event.data.get('dream_summary', '')
                timeline_text += f"  {dream_summary}\n"

            elif event.kind == 'chat_summary':
                summary = event.data.get('summary', '')
                timeline_text += f"  {summary}\n"

            elif event.kind == 'email_response_summary':
                summary = event.data.get('summary', '')
                timeline_text += f"  User shared: {summary}\n"

            timeline_text += "\n"

        return timeline_text

    @staticmethod
    def get_recent_dreams_summary(user, limit=10):
        """
        Get a concise summary of recent dreams from timeline (not full chat logs).

        Args:
            user: User object
            limit: Maximum number of dreams to include

        Returns:
            String summary of recent dreams
        """
        dream_events = TimelineEvent.objects.filter(
            user=user,
            kind='dream'
        ).order_by('-at')[:limit]

        if not dream_events.exists():
            return "No dreams logged yet."

        summary = "RECENT DREAMS:\n\n"

        for i, event in enumerate(reversed(list(dream_events)), 1):
            dream_summary = event.data.get('dream_summary', '')
            date = event.at.strftime('%Y-%m-%d')

            # Find the corresponding chat summary for this dream
            chat_summary = TimelineEvent.objects.filter(
                user=user,
                dream=event.dream,
                kind='chat_summary'
            ).first()

            summary += f"Dream #{i} ({date}):\n"
            summary += f"{dream_summary}\n"

            if chat_summary:
                interp = chat_summary.data.get('summary', '')
                summary += f"Interpretation: {interp}\n"

            summary += "\n"

        return summary
