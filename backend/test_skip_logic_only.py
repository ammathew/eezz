"""
Test the skip logic for public interpretation emails (without actually sending)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Conversation, Message
import uuid

print("=" * 70)
print("TEST: Should Skip Email Logic")
print("=" * 70)

# Function to check if email should be skipped
def should_skip_email(email):
    """Returns True if email should be skipped (user has conversations)"""
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        has_conversations = Conversation.objects.filter(user=existing_user).exists()
        return has_conversations
    return False

# Test 1: Non-existent user
test_email_1 = f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
result_1 = should_skip_email(test_email_1)
print(f"\n[Test 1] Non-existent user")
print(f"  Email: {test_email_1}")
print(f"  Should skip: {result_1}")
print(f"  Result: {'✓ PASS' if not result_1 else '✗ FAIL'}")

# Test 2: User without conversations
test_email_2 = f"noconvo_{uuid.uuid4().hex[:8]}@example.com"
user_2 = User.objects.create_user(
    username=f"user_{uuid.uuid4().hex[:8]}",
    email=test_email_2,
    password='testpass123'
)
result_2 = should_skip_email(test_email_2)
print(f"\n[Test 2] User without conversations")
print(f"  Email: {test_email_2}")
print(f"  User exists: Yes")
print(f"  Has conversations: No")
print(f"  Should skip: {result_2}")
print(f"  Result: {'✓ PASS' if not result_2 else '✗ FAIL'}")

# Test 3: User with conversations
test_email_3 = f"hasconvo_{uuid.uuid4().hex[:8]}@example.com"
user_3 = User.objects.create_user(
    username=f"user_{uuid.uuid4().hex[:8]}",
    email=test_email_3,
    password='testpass123'
)
conversation_3 = Conversation.objects.create(user=user_3, title="Test")
Message.objects.create(conversation=conversation_3, role='user', content='Test')
result_3 = should_skip_email(test_email_3)
print(f"\n[Test 3] User WITH conversations")
print(f"  Email: {test_email_3}")
print(f"  User exists: Yes")
print(f"  Has conversations: Yes")
print(f"  Should skip: {result_3}")
print(f"  Result: {'✓ PASS' if result_3 else '✗ FAIL'}")

# Test 4: User with empty conversation
test_email_4 = f"emptyconvo_{uuid.uuid4().hex[:8]}@example.com"
user_4 = User.objects.create_user(
    username=f"user_{uuid.uuid4().hex[:8]}",
    email=test_email_4,
    password='testpass123'
)
conversation_4 = Conversation.objects.create(user=user_4, title="Empty")
result_4 = should_skip_email(test_email_4)
print(f"\n[Test 4] User WITH empty conversation")
print(f"  Email: {test_email_4}")
print(f"  User exists: Yes")
print(f"  Has conversations: Yes (empty)")
print(f"  Should skip: {result_4}")
print(f"  Result: {'✓ PASS' if result_4 else '✗ FAIL'}")

# Summary
all_pass = (not result_1) and (not result_2) and result_3 and result_4
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Test 1 (no user - should NOT skip): {'PASS' if not result_1 else 'FAIL'}")
print(f"Test 2 (user, no convos - should NOT skip): {'PASS' if not result_2 else 'FAIL'}")
print(f"Test 3 (user with convo - SHOULD skip): {'PASS' if result_3 else 'FAIL'}")
print(f"Test 4 (user with empty convo - SHOULD skip): {'PASS' if result_4 else 'FAIL'}")
print(f"\n{'✓ ALL TESTS PASSED' if all_pass else '✗ SOME TESTS FAILED'}")

# Cleanup
print("\nCleaning up test data...")
User.objects.filter(id__in=[user_2.id, user_3.id, user_4.id]).delete()
print("✓ Test data deleted")
