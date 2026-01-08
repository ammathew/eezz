#!/usr/bin/env python
"""
Test script for email preferences API endpoints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory, force_authenticate
from api.views import get_email_preferences, update_email_preferences

# Get a test user
user = User.objects.filter(email='sunship.space@gmail.com').first()
if not user:
    print("User not found!")
    exit(1)

print(f"Testing with user: {user.email}")
print("=" * 60)

# Test GET preferences
factory = APIRequestFactory()
request = factory.get('/api/preferences/email/')
force_authenticate(request, user=user)

response = get_email_preferences(request)
print(f"\n1. GET /api/preferences/email/")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.data}")

# Test UPDATE preferences
print(f"\n2. POST /api/preferences/email/update/")

# Test updating to 'weekly'
request = factory.post('/api/preferences/email/update/', {'email_frequency': 'weekly'}, format='json')
force_authenticate(request, user=user)

response = update_email_preferences(request)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.data}")

# Verify the update
request = factory.get('/api/preferences/email/')
force_authenticate(request, user=user)
response = get_email_preferences(request)
print(f"\n3. Verify update - GET /api/preferences/email/")
print(f"   Status: {response.status_code}")
print(f"   Current frequency: {response.data.get('email_frequency', 'N/A')}")

# Test invalid frequency
print(f"\n4. Test invalid frequency")
request = factory.post('/api/preferences/email/update/', {'email_frequency': 'invalid_option'}, format='json')
force_authenticate(request, user=user)
response = update_email_preferences(request)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.data}")

print("\n" + "=" * 60)
print("✓ All tests completed!")
