# Timeline-Based Dream Brain - Quick Start Guide

## What Changed?

The Dream Brain now uses **timeline events** instead of full chat logs. This makes daily insights 80% more token-efficient and gives the LLM a cleaner view of each user's dream journey.

## Quick Setup (5 minutes)

### 1. Run the Backfill Command

Create timeline events for existing dreams:

```bash
# Preview what will be created
python manage.py backfill_timeline --dry-run

# Actually create the events
python manage.py backfill_timeline
```

This creates:
- **Dream events**: When each dream was logged
- **Chat summary events**: AI-generated summaries of interpretations

### 2. Test the System

```bash
python test_timeline_system.py
```

This will:
- Create test dream and timeline events
- Query timeline data
- Generate a daily insight using timeline
- Show you exactly how it works

### 3. Verify in Admin

Visit `/admin/dream_brain/timelineevent/` to see the timeline events.

Filter by:
- **Kind**: dream, chat_summary, email_response_summary
- **User**: See specific user's timeline
- **Date**: Timeline events by date

## How It Works Now

### When User Logs a Dream

**File**: `api/views.py`

```python
# First message in conversation triggers:
TimelineService.create_dream_event(user=request.user, conversation=conversation)
```

Creates event:
```json
{
  "kind": "dream",
  "data": {
    "dream_text": "I was flying over a city...",
    "conversation_id": "uuid"
  }
}
```

### When AI Interprets the Dream

**File**: `api/views.py`

```python
# After first AI response:
TimelineService.create_chat_summary_event(user=request.user, conversation=conversation)
```

Creates event with AI-generated summary:
```json
{
  "kind": "chat_summary",
  "data": {
    "summary": "Interpretation revealed themes of freedom and empowerment",
    "key_themes": ["freedom", "control", "transformation"],
    "user_resonance": "User connected this to work stress"
  }
}
```

### When User Replies to Email

**File**: `emails/views.py`

```python
# After processing email response:
TimelineService.create_email_response_summary_event(
    user=daily_insight.user,
    response_content=cleaned_content,
    dream=last_dream,
    source_type='daily_insight'
)
```

Creates event:
```json
{
  "kind": "email_response_summary",
  "data": {
    "summary": "User connected dream to recent promotion",
    "key_points": ["career growth", "feeling empowered"],
    "emotional_tone": "positive",
    "new_connections": "Work promotion mentioned"
  }
}
```

### When Generating Daily Insights

**File**: `dream_brain/services/daily_insight_generator.py`

**Before** (old way):
```python
# Loaded ALL messages from ALL conversations
dreams_summary = self._summarize_all_dreams(conversations)
# Result: 10,000+ tokens of verbose chat logs
```

**After** (new way):
```python
# Uses timeline summaries
dreams_summary = TimelineService.get_recent_dreams_summary(user, limit=10)
full_timeline = TimelineService.get_user_timeline(user, limit=20)
# Result: ~1,750 tokens of distilled story
```

## API Changes

### GET /dream-brain/data/

Now includes timeline data:

```json
{
  "daily_insights": [...],
  "subconscious_insights": [...],
  "patterns": [...],
  "timeline": [
    {
      "id": "uuid",
      "kind": "Dream",
      "at": "2025-01-02T10:30:00Z",
      "data": {
        "dream_text": "...",
        "conversation_id": "uuid"
      },
      "dream_id": "uuid"
    },
    {
      "kind": "Chat Summary",
      "at": "2025-01-02T10:35:00Z",
      "data": {
        "summary": "...",
        "key_themes": [...]
      }
    }
  ]
}
```

## Monitoring & Debugging

### Check Timeline Events

```python
from dream_brain.models import TimelineEvent

# See all events for a user
events = TimelineEvent.objects.filter(user=user).order_by('-at')

# Count events by type
TimelineEvent.objects.filter(kind='dream').count()
TimelineEvent.objects.filter(kind='chat_summary').count()
TimelineEvent.objects.filter(kind='email_response_summary').count()
```

### Get Timeline for LLM Prompt

```python
from dream_brain.services.timeline_service import TimelineService

# Formatted timeline ready for LLM
timeline_text = TimelineService.get_user_timeline(user, limit=20)
print(timeline_text)
```

Output:
```
TIMELINE OF DREAM JOURNEY:

[2025-01-01] Dream:
  Dream: I was flying over a city...

[2025-01-01] Chat Summary:
  Themes of freedom and empowerment emerged
  Themes: freedom, control, transformation

[2025-01-02] Email Response Summary:
  User shared (positive): Connected to recent work promotion
```

### Test Daily Insight

```bash
# Generate insight for specific user
python manage.py send_daily_insights --user email@example.com --dry-run
```

Check the logs - you should see the timeline being used instead of full chat logs.

## Common Tasks

### Backfill for Specific User

```bash
python manage.py backfill_timeline --user annmarynyc@gmail.com
```

### Manually Create Events

```python
from dream_brain.services.timeline_service import TimelineService

# For a dream
TimelineService.create_dream_event(user, conversation)

# For interpretation summary
TimelineService.create_chat_summary_event(user, conversation)

# For email response
TimelineService.create_email_response_summary_event(
    user=user,
    response_content="User's reply text",
    dream=conversation,  # optional
    source_type='daily_insight'
)
```

### Query Timeline Stats

```python
from dream_brain.models import TimelineEvent

# Events by user
user_events = TimelineEvent.objects.filter(user=user)

# Recent events
recent = TimelineEvent.objects.order_by('-at')[:10]

# Events for specific dream
dream_events = TimelineEvent.objects.filter(dream=conversation)
```

## Troubleshooting

### Timeline events not being created?

**Check**: Are the hooks in place?
- `api/views.py` line 146-150 (dream events)
- `api/views.py` line 185-193 (chat summaries)
- `emails/views.py` line 267-275 (email responses)

**Verify**: Check Django logs for errors

### Daily insights still using full chat logs?

**Check**: `dream_brain/services/daily_insight_generator.py` line 91-94

Should see:
```python
dreams_summary = TimelineService.get_recent_dreams_summary(user, limit=10)
full_timeline = TimelineService.get_user_timeline(user, limit=20)
```

### Want to regenerate summaries?

Timeline events are created once. To regenerate:
1. Delete existing events: `TimelineEvent.objects.filter(user=user).delete()`
2. Run backfill: `python manage.py backfill_timeline --user email@example.com`

## Next Steps

1. ✅ Run backfill command
2. ✅ Verify events in admin
3. ✅ Test with test script
4. 🔄 Monitor new dreams (should auto-create events)
5. 🔄 Test daily insight generation
6. 🔄 Test email responses

## Documentation

- **Architecture**: See `TIMELINE_ARCHITECTURE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **This Guide**: `QUICK_START.md`

## Support

Questions? Check:
1. Timeline events in admin: `/admin/dream_brain/timelineevent/`
2. Logs for timeline service calls
3. Run test suite: `python test_timeline_system.py`
