#!/usr/bin/env python
"""
Test script for process_stale_conversations task.
Tests the new scheduled task that creates timeline events for stale conversations.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from dream_brain.tasks import process_stale_conversations

print("=" * 60)
print("TESTING PROCESS STALE CONVERSATIONS TASK")
print("=" * 60)
print()

# Run the task
result = process_stale_conversations()

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)
print(f"Status: {result.get('status')}")
print(f"Conversations found: {result.get('conversations_found', 0)}")
print(f"Dream events created: {result.get('dream_events_created', 0)}")
print(f"Chat summaries created: {result.get('chat_summaries_created', 0)}")
print(f"Errors: {result.get('errors', 0)}")

if result.get('status') == 'error':
    print(f"Error: {result.get('error')}")

print("=" * 60)
