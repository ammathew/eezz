# Django Q Deployment Guide

This guide explains how to deploy the Django Q task queue for sending daily insight emails.

## What Was Set Up

### 1. Installed Django Q
```bash
pip install django-q2==1.7.4
```

### 2. Configuration
Added to `config/settings.py`:
- `'django_q'` in INSTALLED_APPS
- Q_CLUSTER configuration at the bottom

### 3. Created Scheduled Task
- **File**: `dream_brain/tasks.py`
- **Function**: `send_daily_insights()`
- **Schedule**: Daily at 9 AM (cron: `0 9 * * *`)
- **What it does**:
  1. Finds all users eligible for daily insights (have dreams, 24+ hours since last)
  2. Filters by email frequency preferences (daily, every 2 days, weekly, etc.)
  3. Generates personalized insights
  4. Sends emails via Postmark

### 4. Management Commands
- `python manage.py setup_schedules` - Sets up the daily email schedule
- `python manage.py qcluster` - Runs the task queue worker

## Deployment Steps

### On Production Server

1. **Install Django Q**:
```bash
pip install django-q2==1.7.4
```

2. **Run migrations**:
```bash
python manage.py migrate
```

3. **Set up the schedule**:
```bash
python manage.py setup_schedules
```

This creates a cron schedule that runs at 9 AM daily.

4. **Start the Django Q cluster** (as a background service):

You have two options:

#### Option A: Using systemd (recommended for production)

Create `/etc/systemd/system/djangoq.service`:

```ini
[Unit]
Description=Django Q Cluster
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/backend
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/path/to/your/venv/bin/python manage.py qcluster
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable djangoq
sudo systemctl start djangoq
sudo systemctl status djangoq
```

#### Option B: Using supervisor

Create `/etc/supervisor/conf.d/djangoq.conf`:

```ini
[program:djangoq]
command=/path/to/your/venv/bin/python manage.py qcluster
directory=/path/to/your/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/djangoq.log
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start djangoq
```

## Monitoring

### Check schedules:
```bash
python manage.py shell
>>> from django_q.models import Schedule
>>> for s in Schedule.objects.all():
...     print(f"{s.name}: {s.get_schedule_type_display()}, next run: {s.next_run}")
```

### Check task history:
```bash
python manage.py shell
>>> from django_q.models import Task
>>> Task.objects.filter(func='dream_brain.tasks.send_daily_insights').order_by('-started')[:5]
```

### View logs:
The task logs to Django's logging system. Check your application logs for:
- `DREAM BRAIN - DAILY INSIGHTS TASK`
- Task execution summaries

## Testing

### Test the task manually:
```bash
python manage.py shell
>>> from dream_brain.tasks import send_daily_insights
>>> result = send_daily_insights()
>>> print(result)
```

### Test with specific user:
```bash
python manage.py send_daily_insights --user user@example.com --dry-run
```

## Email Frequency Settings

Users can control email frequency in their profile at https://app.unravel.so/profile:
- Off - No emails
- Daily
- Every 2 days
- Every 3 days
- Every 5 days
- Weekly

The task respects these settings automatically via `dream_brain.services.email_scheduler.filter_users_by_email_preference()`.

## Troubleshooting

### Task not running?
1. Check Django Q cluster is running: `ps aux | grep qcluster`
2. Check schedule exists: `python manage.py shell` → `Schedule.objects.all()`
3. Check logs for errors

### Emails not sending?
1. Check POSTMARK_API_KEY is set in environment
2. Check user email preferences in database
3. Run task manually to see detailed logs

### Change schedule time:
```bash
python manage.py shell
>>> from django_q.models import Schedule
>>> s = Schedule.objects.get(name='send_daily_insights')
>>> s.cron = '0 10 * * *'  # Change to 10 AM
>>> s.save()
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Django Q Cluster                         │
│                  (python manage.py qcluster)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Checks schedules every minute
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Schedule: send_daily_insights                   │
│              Cron: 0 9 * * * (9 AM daily)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Triggers
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Task: dream_brain.tasks.send_daily_insights()      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ Find eligible│  │ Filter by email  │  │ Generate &      │
│ users (24h+) │─>│ frequency prefs  │─>│ send insights   │
└──────────────┘  └──────────────────┘  └─────────────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Postmark Email  │
                                        │ Service         │
                                        └─────────────────┘
```
