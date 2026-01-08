from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Conversation, Message


class Command(BaseCommand):
    help = 'Display all conversations and messages for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')

    def handle(self, *args, **options):
        email = options['email']
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email "{email}" not found'))
            return

        conversations = Conversation.objects.filter(user=user).order_by('created_at')

        if not conversations.exists():
            self.stdout.write(self.style.WARNING(f'No conversations found for {email}'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nConversations for {email}:\n'))

        for conv in conversations:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(f"CONVERSATION: {conv.title}")
            self.stdout.write(f"Created: {conv.created_at}")
            self.stdout.write(f"{'='*80}\n")

            messages = conv.messages.all().order_by('created_at')
            for msg in messages:
                self.stdout.write(f"[{msg.created_at}] {msg.role.upper()}:")
                self.stdout.write(msg.content)
                self.stdout.write(f"\n{'-'*80}\n")

        self.stdout.write(self.style.SUCCESS(f'\nTotal conversations: {conversations.count()}'))
