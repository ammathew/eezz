"""
Test that public interpretation emails are NOT sent to app users with conversations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import PublicDreamSubmission, Conversation, Message
from api.email_service import EmailService
from django.utils import timezone
import uuid

print("=" * 70)
print("TEST: Public Interpretation Email Filtering")
print("=" * 70)

# Test 1: Email for non-existent user (should send)
print("\n[Test 1] Email to non-existent user (should send)")
test_email_1 = f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
submission_1 = PublicDreamSubmission.objects.create(
    dream_text="Test dream 1",
    email=test_email_1,
    interpretation="Test interpretation 1",
    status='processing'
)
result_1 = EmailService.send_dream_interpretation(submission_1)
submission_1.refresh_from_db()
print(f"  Email: {test_email_1}")
print(f"  Status: {submission_1.status}")
print(f"  Result: {'✓ PASS - Email would be sent' if submission_1.status == 'sent' else '✗ FAIL - Email was not sent'}")

# Test 2: Email for existing user WITHOUT conversations (should send)
print("\n[Test 2] Email to user without conversations (should send)")
test_email_2 = f"noconvo_{uuid.uuid4().hex[:8]}@example.com"
user_2 = User.objects.create_user(
    username=f"user_{uuid.uuid4().hex[:8]}",
    email=test_email_2,
    password='testpass123'
)
submission_2 = PublicDreamSubmission.objects.create(
    dream_text="Test dream 2",
    email=test_email_2,
    interpretation="Test interpretation 2",
    status='processing'
)
result_2 = EmailService.send_dream_interpretation(submission_2)
submission_2.refresh_from_db()
print(f"  Email: {test_email_2}")
print(f"  User exists: Yes")
print(f"  Has conversations: No")
print(f"  Status: {submission_2.status}")
print(f"  Result: {'✓ PASS - Email would be sent' if submission_2.status == 'sent' else '✗ FAIL - Email was not sent'}")

# Test 3: Email for existing user WITH conversations (should NOT send)
print("\n[Test 3] Email to user WITH conversations (should NOT send)")
test_email_3 = f"hasconvo_{uuid.uuid4().hex[:8]}@example.com"
user_3 = User.objects.create_user(
    username=f"user_{uuid.uuid4().hex[:8]}",
    email=test_email_3,
    password='testpass123'
)
# Create a conversation with messages
conversation_3 = Conversation.objects.create(
    user=user_3,
    title="Test Conversation"
)
Message.objects.create(
    conversation=conversation_3,
    role='user',
    content='Test message'
)
submission_3 = PublicDreamSubmission.objects.create(
    dream_text="Test dream 3",
    email=test_email_3,
    interpretation="Test interpretation 3",
    status='processing'
)
result_3 = EmailService.send_dream_interpretation(submission_3)
submission_3.refresh_from_db()
print(f"  Email: {test_email_3}")
print(f"  User exists: Yes")
print(f"  Has conversations: Yes")
print(f"  Status: {submission_3.status}")
print(f"  Result: {'✓ PASS - Email was skipped' if submission_3.status == 'skipped' else '✗ FAIL - Email was sent when it should have been skipped'}")

# Test 4: Email for existing user WITH empty conversation (should NOT send)
print("\n[Test 4] Email to user WITH empty conversation (should NOT send)")
test_email_4 = f"emptyconvo_{uuid.uuid4().hex[:8]}@example.com"
user_4 = User.objects.create_user(
    username=f"user_{uuid.uuid4().hex[:8]}",
    email=test_email_4,
    password='testpass123'
)
# Create conversation but no messages
conversation_4 = Conversation.objects.create(
    user=user_4,
    title="Empty Conversation"
)
submission_4 = PublicDreamSubmission.objects.create(
    dream_text="Test dream 4",
    email=test_email_4,
    interpretation="Test interpretation 4",
    status='processing'
)
result_4 = EmailService.send_dream_interpretation(submission_4)
submission_4.refresh_from_db()
print(f"  Email: {test_email_4}")
print(f"  User exists: Yes")
print(f"  Has conversations: Yes (empty)")
print(f"  Status: {submission_4.status}")
print(f"  Result: {'✓ PASS - Email was skipped' if submission_4.status == 'skipped' else '✗ FAIL - Email was sent when it should have been skipped'}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Test 1 (no user): {'PASS' if submission_1.status == 'sent' else 'FAIL'}")
print(f"Test 2 (user, no convos): {'PASS' if submission_2.status == 'sent' else 'FAIL'}")
print(f"Test 3 (user with convo): {'PASS' if submission_3.status == 'skipped' else 'FAIL'}")
print(f"Test 4 (user with empty convo): {'PASS' if submission_4.status == 'skipped' else 'FAIL'}")

# Cleanup
print("\nCleaning up test data...")
PublicDreamSubmission.objects.filter(submission_id__in=[
    submission_1.submission_id,
    submission_2.submission_id,
    submission_3.submission_id,
    submission_4.submission_id
]).delete()
User.objects.filter(id__in=[user_2.id, user_3.id, user_4.id]).delete()
print("✓ Test data deleted")
