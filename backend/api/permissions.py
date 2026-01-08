from rest_framework import permissions
from .models import HijackSession


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class to check if user is a superadmin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsSuperAdminOrHijacking(permissions.BasePermission):
    """
    Permission class that allows access if:
    - User is a superadmin, OR
    - User is being viewed through an active hijack session

    Security: Validates IP address and User-Agent to prevent token theft
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is superadmin
        if request.user.is_superuser:
            return True

        # Check if there's an active hijack session for this user
        # Look for hijack token in request headers or session
        hijack_token = request.headers.get('X-Hijack-Token')

        if hijack_token:
            try:
                hijack_session = HijackSession.objects.get(
                    session_token=hijack_token,
                    target_user=request.user,
                    is_active=True
                )

                # Security checks
                # 1. Check if session is not expired
                if hijack_session.is_expired():
                    return False

                # 2. Verify IP address matches (prevents token theft from different location)
                current_ip = request.META.get('REMOTE_ADDR')
                if hijack_session.ip_address != current_ip:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"SECURITY: IP mismatch for hijack session {hijack_session.session_token}. "
                        f"Expected: {hijack_session.ip_address}, Got: {current_ip}"
                    )
                    return False

                # 3. Verify User-Agent matches (prevents token theft from different browser)
                current_ua = request.META.get('HTTP_USER_AGENT', '')[:500]
                if hijack_session.user_agent != current_ua:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"SECURITY: User-Agent mismatch for hijack session {hijack_session.session_token}"
                    )
                    return False

                return True

            except HijackSession.DoesNotExist:
                pass

        return False
