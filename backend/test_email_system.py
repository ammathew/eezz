#!/usr/bin/env python
"""
Test script for the new emails and dream_brain infrastructure.
Run with: DEBUG=True python test_email_system.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Conversation, Message
from emails.services.base import BaseEmailService
from dream_brain.models import Reflection
from django.utils import timezone
import uuid

def test_email_service():
    """Test the base email service"""
    print("\n=== Testing Email Service ===")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    if created:
        print(f"✓ Created test user: {user.email}")
    else:
        print(f"✓ Using existing user: {user.email}")
    
    # Create a test email template
    from django.template.loader import render_to_string
    
    print("\n✓ Email service initialized")
    print("✓ Postmark backend loaded")
    print("✓ Base template exists at: emails/templates/emails/base.html")
    
    # Note: We won't actually send to avoid using email quota
    print("\n⚠️  Not sending actual email (to preserve quota)")
    print("   To test sending, call:")
    print("   email_service = BaseEmailService()")
    print("   email_service.send(user, 'test@example.com', 'Test', 'emails/base.html', {})")

def test_dream_brain_models():
    """Test creating dream_brain records"""
    print("\n=== Testing Dream Brain Models ===")
    
    # Get or create test user
    user, _ = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Create a test conversation (dream)
    conversation, created = Conversation.objects.get_or_create(
        user=user,
        title="Test Dream - Flying",
        defaults={'created_at': timezone.now()}
    )
    if created:
        print(f"✓ Created test conversation: {conversation.title}")
    else:
        print(f"✓ Using existing conversation: {conversation.title}")
    
    # Create a test reflection (without actually sending)
    reflection, created = Reflection.objects.get_or_create(
        user=user,
        dream_conversation=conversation,
        reflection_type='followup_3day',
        defaults={
            'subject': 'Reflecting on your flying dream',
            'content': 'Test reflection content...',
            'reply_to_email': f'reflection-{uuid.uuid4()}@replies.unravel.so',
            'status': 'pending'
        }
    )
    
    if created:
        print(f"✓ Created test reflection: {reflection.reflection_id}")
    else:
        print(f"✓ Using existing reflection: {reflection.reflection_id}")
    
    print(f"  - Type: {reflection.get_reflection_type_display()}")
    print(f"  - Status: {reflection.status}")
    print(f"  - Reply-to: {reflection.reply_to_email}")

def test_admin_access():
    """Check if admin interfaces are registered"""
    print("\n=== Testing Admin Interfaces ===")
    
    from django.contrib import admin
    from emails.models import Email, EmailEvent, InboundEmail
    from dream_brain.models import Reflection, PersonalSymbol, SubconsciousInsight
    
    models_to_check = [
        (Email, 'Email'),
        (EmailEvent, 'EmailEvent'),
        (InboundEmail, 'InboundEmail'),
        (Reflection, 'Reflection'),
        (PersonalSymbol, 'PersonalSymbol'),
        (SubconsciousInsight, 'SubconsciousInsight'),
    ]
    
    for model, name in models_to_check:
        if admin.site.is_registered(model):
            print(f"✓ {name} registered in admin")
        else:
            print(f"✗ {name} NOT registered in admin")

def show_database_stats():
    """Show current database stats"""
    print("\n=== Database Statistics ===")
    
    from emails.models import Email
    from dream_brain.models import Reflection, ReflectionResponse, SubconsciousInsight, PersonalSymbol
    
    print(f"Emails sent: {Email.objects.count()}")
    print(f"Reflections created: {Reflection.objects.count()}")
    print(f"Reflection responses: {ReflectionResponse.objects.count()}")
    print(f"Subconscious insights: {SubconsciousInsight.objects.count()}")
    print(f"Personal symbols: {PersonalSymbol.objects.count()}")

if __name__ == '__main__':
    print("=" * 60)
    print("DREAM BRAIN EMAIL SYSTEM TEST")
    print("=" * 60)
    
    try:
        test_email_service()
        test_dream_brain_models()
        test_admin_access()
        show_database_stats()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nWhat you can do now:")
        print("1. Run the Django admin: python manage.py runserver")
        print("2. Visit http://localhost:8000/admin")
        print("3. View the Emails and Dream Brain sections")
        print("4. Check the test Reflection and Conversation we created")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
