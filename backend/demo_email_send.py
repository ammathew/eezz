#!/usr/bin/env python
"""
Demo: Actually send a test email through the new system.
This will send a REAL email, so only run when you're ready!

Run with: DEBUG=True python demo_email_send.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from emails.services.base import BaseEmailService
from django.template.loader import render_to_string

def send_test_email():
    """Send a real test email"""
    
    # Get test user
    user = User.objects.filter(username='test_user').first()
    if not user:
        print("No test user found. Run test_email_system.py first!")
        return
    
    # Initialize email service
    email_service = BaseEmailService()
    
    # Create a simple test email
    test_template = """
{% extends "emails/base.html" %}
{% block content %}
<h2>Test Email from Dream Brain System</h2>
<p>Hi there!</p>
<p>This is a test email from your new Dream Brain email infrastructure.</p>
<p>If you're seeing this, it means:</p>
<ul>
    <li>✓ Email models are working</li>
    <li>✓ Email service is working</li>
    <li>✓ Postmark backend is working</li>
    <li>✓ Template rendering is working</li>
</ul>
<p>
    <a href="{{ frontend_url }}" class="button">Visit Unravel</a>
</p>
{% endblock %}
"""
    
    # Save test template temporarily
    import tempfile
    import shutil
    from pathlib import Path
    
    template_dir = Path('emails/templates/emails')
    template_path = template_dir / 'test_email.html'
    
    with open(template_path, 'w') as f:
        f.write(test_template)
    
    print("Sending test email...")
    print(f"To: {user.email}")
    
    # Send the email
    email = email_service.send(
        user=user,
        recipient_email=user.email,
        subject="Test Email - Dream Brain System",
        template_name='emails/test_email.html',
        context={
            'user_name': user.username,
        },
        email_type='system'
    )
    
    if email:
        print(f"\n✓ Email sent successfully!")
        print(f"  Email ID: {email.email_id}")
        print(f"  Status: {email.status}")
        print(f"  Sent at: {email.sent_at}")
        print(f"\nCheck the Django admin to see the Email record.")
    else:
        print("\n✗ Email failed to send. Check logs for details.")

if __name__ == '__main__':
    print("=" * 60)
    print("DREAM BRAIN - EMAIL SENDING DEMO")
    print("=" * 60)
    print("\n⚠️  WARNING: This will send a REAL email!")
    
    response = input("\nProceed? (yes/no): ")
    if response.lower() == 'yes':
        send_test_email()
    else:
        print("Cancelled.")
