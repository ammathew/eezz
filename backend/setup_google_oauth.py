#!/usr/bin/env python
"""
Script to set up Google OAuth in Django admin
Run this after you have your Google OAuth credentials
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config

def setup_google_oauth():
    print("🔧 Setting up Google OAuth...")

    # Get credentials from environment
    client_id = config('GOOGLE_OAUTH_CLIENT_ID', default='')
    client_secret = config('GOOGLE_OAUTH_CLIENT_SECRET', default='')

    if not client_id or not client_secret:
        print("❌ Error: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set in .env")
        print("   Please add them to backend/.env and try again")
        return False

    # Get or create site
    site, created = Site.objects.get_or_create(
        pk=1,
        defaults={'domain': 'localhost:8000', 'name': 'Unravel'}
    )

    if created:
        print(f"✅ Created site: {site.domain}")
    else:
        print(f"✅ Using existing site: {site.domain}")
        # Update the site to ensure it's correct
        site.domain = 'localhost:8000'
        site.name = 'Unravel'
        site.save()

    # Get or create Google social app
    google_app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={
            'name': 'Google OAuth',
            'client_id': client_id,
            'secret': client_secret,
        }
    )

    if created:
        print(f"✅ Created Google OAuth app")
        google_app.sites.add(site)
    else:
        print(f"✅ Using existing Google OAuth app")
        # Update the credentials
        google_app.client_id = client_id
        google_app.secret = client_secret
        google_app.save()
        google_app.sites.add(site)

    print("\n✨ Google OAuth setup complete!")
    print("\n📝 Next steps:")
    print("1. Make sure you've added these redirect URIs in Google Cloud Console:")
    print("   - http://localhost:8000/accounts/google/login/callback/")
    print("   - http://localhost:8000/api/auth/google/callback/")
    print("2. Restart your Django server")
    print("3. Click 'Continue with Google' on the login page")
    print("\n🔗 Authorized origins in Google Console should include:")
    print("   - http://localhost:5173")
    print("   - http://localhost:8000")

    return True

if __name__ == '__main__':
    setup_google_oauth()
