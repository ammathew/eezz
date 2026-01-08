from django.contrib.auth import get_user_model
from api.models import Conversation, Message

User = get_user_model()
user = User.objects.get(email='toni.lynn.m.1990@gmail.com')

conversations = Conversation.objects.filter(user=user).order_by('created_at')

for conv in conversations:
    print(f"\n{'='*80}")
    print(f"CONVERSATION: {conv.title}")
    print(f"Created: {conv.created_at}")
    print(f"{'='*80}\n")

    messages = conv.messages.all().order_by('created_at')
    for msg in messages:
        print(f"[{msg.created_at}] {msg.role.upper()}:")
        print(msg.content)
        print(f"\n{'-'*80}\n")