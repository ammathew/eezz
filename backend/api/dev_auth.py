from decouple import config
from django.conf import settings
from django.contrib.auth.models import User


def resolve_request_user(request):
    if request.user and request.user.is_authenticated:
        return request.user

    if not settings.DEBUG:
        return None

    if not config('DEV_BYPASS_AUTH', default=False, cast=bool):
        return None

    email = config('DEV_BYPASS_USER_EMAIL', default='dev@local').strip()
    username = email or 'dev@local'
    user, _created = User.objects.get_or_create(
        username=username,
        defaults={'email': email or ''},
    )
    return user
