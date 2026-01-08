from django.core.management.base import BaseCommand
from api.models import Conversation

class Command(BaseCommand):
    help = 'Delete conversations with 0 messages'

    def handle(self, *args, **options):
        # Find conversations with no messages
        empty_conversations = Conversation.objects.filter(messages__isnull=True).distinct()
        count = empty_conversations.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No empty conversations found'))
            return
        
        self.stdout.write(f'Found {count} empty conversations')
        
        # Delete them
        empty_conversations.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} empty conversations'))
