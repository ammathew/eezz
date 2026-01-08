from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserProfile

class Command(BaseCommand):
    help = 'Creates a UserProfile for any user that does not have one.'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        count = 0
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            count += 1
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully created {count} missing user profiles.'))
        else:
            self.stdout.write(self.style.SUCCESS('All users already have a profile.'))
