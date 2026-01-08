from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from api.models import Conversation, UserProfile


class Command(BaseCommand):
    help = 'Clean up duplicate users with the same email'

    def handle(self, *args, **options):
        # Find duplicate emails
        duplicates = User.objects.values('email').annotate(count=Count('id')).filter(count__gt=1)

        for dup in duplicates:
            email = dup['email']
            self.stdout.write(f"\nProcessing email: {email}")

            # Get all users with this email, ordered by ID (oldest first)
            users = list(User.objects.filter(email=email).order_by('id'))

            # Keep the user with the most recent last_login, or the newest if none have logged in
            users_with_login = [u for u in users if u.last_login]
            if users_with_login:
                # Keep the one with most recent login
                keep_user = max(users_with_login, key=lambda u: u.last_login)
            else:
                # Keep the newest (highest ID)
                keep_user = users[-1]

            self.stdout.write(f"  Keeping user ID {keep_user.id} (username: {keep_user.username})")

            # Merge data from other users to the keeper
            for user in users:
                if user.id == keep_user.id:
                    continue

                self.stdout.write(f"  Merging user ID {user.id} into {keep_user.id}...")

                # Move conversations
                conversation_count = Conversation.objects.filter(user=user).update(user=keep_user)
                if conversation_count:
                    self.stdout.write(f"    - Moved {conversation_count} conversations")

                # Handle user profile
                try:
                    old_profile = user.profile
                    # If keeper doesn't have a profile, move the old one
                    try:
                        keep_profile = keep_user.profile
                    except UserProfile.DoesNotExist:
                        old_profile.user = keep_user
                        old_profile.save()
                        self.stdout.write(f"    - Moved profile")
                    else:
                        # Keeper has profile, delete the old one
                        old_profile.delete()
                        self.stdout.write(f"    - Deleted duplicate profile")
                except UserProfile.DoesNotExist:
                    pass

                # Delete the duplicate user
                user.delete()
                self.stdout.write(f"    - Deleted user ID {user.id}")

        self.stdout.write(self.style.SUCCESS('\nCleanup complete!'))
