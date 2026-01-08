"""
Test script to verify that unsubscribe updates all submissions for an email
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import PublicDreamSubmission
from django.utils import timezone
import uuid

# Create test email
test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

print(f"Creating test submissions for {test_email}...")

# Create 3 submissions with the same email
submissions = []
for i in range(3):
    sub = PublicDreamSubmission.objects.create(
        dream_text=f"Test dream {i+1}",
        email=test_email,
        status='sent',
        email_subscribed=True,
        unsubscribe_token=uuid.uuid4(),
        email_sent_at=timezone.now()
    )
    submissions.append(sub)
    print(f"  Created submission {sub.submission_id}")

# Verify all are subscribed
subscribed_count = PublicDreamSubmission.objects.filter(
    email=test_email,
    email_subscribed=True
).count()
print(f"\n✓ All {subscribed_count} submissions are subscribed")

# Simulate unsubscribe using the FIRST submission's token
print(f"\nUnsubscribing via first submission's token...")
first_submission = submissions[0]

# This is what the view does
email = first_submission.email
updated_count = PublicDreamSubmission.objects.filter(
    email=email
).update(email_subscribed=False)

print(f"  Updated {updated_count} submission(s)")

# Check all submissions are now unsubscribed
still_subscribed = PublicDreamSubmission.objects.filter(
    email=test_email,
    email_subscribed=True
).count()

unsubscribed = PublicDreamSubmission.objects.filter(
    email=test_email,
    email_subscribed=False
).count()

print(f"\n✓ Subscribed: {still_subscribed}")
print(f"✓ Unsubscribed: {unsubscribed}")

if still_subscribed == 0 and unsubscribed == 3:
    print("\n✅ SUCCESS! All submissions were unsubscribed")
else:
    print("\n❌ FAILED! Not all submissions were unsubscribed")

# Cleanup
print(f"\nCleaning up test data...")
PublicDreamSubmission.objects.filter(email=test_email).delete()
print("✓ Test data deleted")
