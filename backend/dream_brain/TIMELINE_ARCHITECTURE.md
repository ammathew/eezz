# Dream Brain Timeline Architecture

## Overview

The Dream Brain has been refactored to use **timeline-based events** instead of full chat logs. This creates a cleaner, more efficient system where the LLM sees a distilled story of the user's dream journey rather than verbose chat transcripts.

## Core Concept

**Timeline = The Distilled Story**

Instead of feeding the LLM every chat message ever exchanged, we create a timeline of key events:
- Dreams logged
- Chat summaries (what the interpretation revealed)
- Email response summaries (what the user shared back)

This approach:
- Reduces token usage significantly
- Focuses on what matters: the story arc and user insights
- Makes the context cleaner and more actionable for daily insights

## Models

### TimelineEvent

The central model that stores distilled events in a user's dream journey.

```python
class TimelineEvent(models.Model):
    user = FK(User)
    dream = FK(Conversation, null=True, blank=True)  # Optional link to dream
    kind = CharField(choices=['dream', 'chat_summary', 'email_response_summary'])
    at = DateTimeField()  # When this event occurred
    data = JSONField()  # Concise structured info
```

#### Event Types

1. **dream**: User logged a dream
   ```json
   {
     "dream_text": "I was flying over a city...",
     "conversation_id": "uuid"
   }
   ```

2. **chat_summary**: Summary of dream interpretation conversation
   ```json
   {
     "summary": "The interpretation revealed themes of freedom and control",
     "key_themes": ["freedom", "control", "transformation"],
     "user_resonance": "User connected this to recent job stress"
   }
   ```

3. **email_response_summary**: User replied to a daily insight or reflection
   ```json
   {
     "summary": "User shared that the dream pattern aligns with therapy progress",
     "key_points": ["therapy connection", "feeling empowered"],
     "emotional_tone": "positive",
     "new_connections": "Linked to recent promotion at work",
     "source_type": "daily_insight"
   }
   ```

### DailyInsightResponse

New model to track user replies to daily insights (parallel to ReflectionResponse).

```python
class DailyInsightResponse(models.Model):
    daily_insight = FK(DailyInsight)
    user = FK(User)
    raw_content = TextField()
    cleaned_content = TextField()
    processed = BooleanField(default=False)
```

## Services

### TimelineService

Helper service for creating and querying timeline events.

#### Key Methods

**Creating Events:**
- `create_dream_event(user, conversation)` - When a dream is logged
- `create_chat_summary_event(user, conversation)` - After interpretation chat
- `create_email_response_summary_event(user, response_content, dream, source_type)` - When user replies

**Querying Timeline:**
- `get_user_timeline(user, limit=20, dream=None)` - Get formatted timeline for LLM prompts
- `get_recent_dreams_summary(user, limit=10)` - Get concise dream summaries (not full chats)

### DailyInsightGenerator (Updated)

The daily insight generator now uses timeline events instead of full chat logs.

**Before:**
```python
# Old approach: Summarize ALL chat messages
dreams_summary = self._summarize_all_dreams(conversations)
```

**After:**
```python
# New approach: Use timeline summaries
dreams_summary = TimelineService.get_recent_dreams_summary(user, limit=10)
full_timeline = TimelineService.get_user_timeline(user, limit=20)
```

## When to Create Timeline Events

### On Dream Logging (API/Chat)
```python
# After user submits a dream
conversation = Conversation.objects.create(user=user, title=title)
Message.objects.create(conversation=conversation, role='user', content=dream_text)

# Create timeline event
TimelineService.create_dream_event(user, conversation)
```

### After Interpretation Chat
```python
# After the AI interpretation is complete and conversation ends
# (Could be triggered when user ends chat, or after N messages)
TimelineService.create_chat_summary_event(user, conversation)
```

### On Email Responses
```python
# When processing inbound email from daily insight reply
daily_insight_response = DailyInsightResponse.objects.create(...)

# Create timeline event
TimelineService.create_email_response_summary_event(
    user=user,
    response_content=daily_insight_response.cleaned_content,
    dream=None,  # Daily insights are about all dreams
    source_type='daily_insight'
)
```

## Where Full Conversations Go

**Option 1 (Current):** Keep Message table but don't use it in daily insights
- Full chat messages still exist in `Message` model
- Timeline only stores summaries
- You can always view the full chat if needed for debugging

**Option 2 (Future):** Store only last N messages
- Keep last 3-5 messages per conversation for context
- Older messages can be archived or deleted

**Option 3 (Minimal):** Don't store chat at all
- After each conversation, immediately:
  - Generate `chat_summary` event
  - Discard raw messages
- Future prompts use only timeline summaries

## LLM Context for Daily Insights

The LLM now receives:

```
RECENT DREAMS:
Dream #1 (2025-01-01):
I was flying over a city...
Interpretation: This dream suggests themes of freedom and empowerment...

Dream #2 (2024-12-28):
I was back in high school...
Interpretation: Common anxiety dream about performance pressure...

TIMELINE OF DREAM JOURNEY:
[2024-12-28] Dream: I was back in high school...
[2024-12-28] Chat Summary: Interpretation revealed performance anxiety themes
[2024-12-29] Email Response Summary: User shared (positive): Connected to upcoming work presentation
[2025-01-01] Dream: I was flying over a city...
[2025-01-01] Chat Summary: Themes of freedom and control emerged

DREAM BRAIN KNOWLEDGE BASE:
(Patterns, insights from ReflectionResponse processing)
```

**Not included:** Full chat transcripts with every "User: ...", "AI: ..." message

## Migration & Backfill

### For Existing Dreams

Run the backfill command to create timeline events for existing dreams:

```bash
# Dry run to see what would be created
python manage.py backfill_timeline --dry-run

# Actually create events
python manage.py backfill_timeline

# For specific user
python manage.py backfill_timeline --user user@example.com
```

This will:
1. Create `dream` events for all existing conversations
2. Create `chat_summary` events for conversations with multiple messages
3. Skip events that already exist (idempotent)

### Going Forward

Integrate timeline event creation into:
- Dream submission flow (create `dream` event)
- Chat completion (create `chat_summary` event)
- Email reply processing (create `email_response_summary` event)

## Benefits

1. **Token Efficiency**: Send only summaries, not full transcripts
2. **Cleaner Context**: LLM sees the story arc, not verbose back-and-forth
3. **Scalability**: Timeline stays manageable even with 100+ dreams
4. **Flexibility**: Easy to add new event types as needed
5. **Debugging**: Timeline shows the condensed narrative at a glance

## Admin Interface

New admin views:
- **TimelineEvent**: Browse all timeline events by user/date/kind
- **DailyInsightResponse**: Track user replies to daily insights

Filter by:
- Event kind (dream, chat_summary, email_response_summary)
- Date range
- User
- Associated dream

## Future Enhancements

1. **Auto-summarization**: Trigger `chat_summary` creation when conversation goes idle
2. **Event Deduplication**: Prevent duplicate events
3. **Timeline Visualization**: Show user's dream journey as a visual timeline
4. **Pattern Detection**: Analyze timeline to auto-detect patterns
5. **Contextual Insights**: Reference specific timeline events in daily insights
