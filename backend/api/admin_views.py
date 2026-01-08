from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .permissions import IsSuperAdmin, IsSuperAdminOrHijacking
from .serializers import UserSerializer
from .models import HijackSession
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class HijackRateThrottle(UserRateThrottle):
    """Custom rate throttle: 10 hijacks per minute"""
    rate = '10/min'


class StartHijackSessionView(APIView):
    """
    Starts a hijack session - superadmin can view as another user.
    POST /api/admin/hijack/start/<user_id>/
    Returns a hijack session token instead of user JWT tokens.

    Rate limited to 10 hijacks per minute for security.
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOrHijacking]
    throttle_classes = [HijackRateThrottle]

    def post(self, request, user_id):
        try:
            # Determine the actual admin user
            # If in hijack mode, get admin from hijack session
            # Otherwise, current user must be superuser
            actual_admin = request.user

            hijack_token = request.headers.get('X-Hijack-Token')
            if hijack_token and not request.user.is_superuser:
                # User is in hijack mode, get the real admin
                try:
                    existing_session = HijackSession.objects.get(
                        session_token=hijack_token,
                        target_user=request.user,
                        is_active=True
                    )
                    actual_admin = existing_session.admin_user
                    # End the old hijack session
                    existing_session.end_session()
                    logger.info(
                        f"Ended previous hijack session {existing_session.session_token} "
                        f"before starting new one"
                    )
                except HijackSession.DoesNotExist:
                    pass

            # Get the target user
            target_user = User.objects.get(id=user_id)

            # Prevent hijacking another superuser
            if target_user.is_superuser and target_user.id != actual_admin.id:
                logger.warning(
                    f"BLOCKED: Admin '{actual_admin.email}' attempted to hijack "
                    f"superuser '{target_user.email}'"
                )
                return Response(
                    {'error': 'Cannot hijack another superuser for security reasons'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create NEW hijack session with the actual admin
            hijack_session = HijackSession.objects.create(
                admin_user=actual_admin,
                target_user=target_user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
            )

            # Log the action for security audit
            logger.warning(
                f"HIJACK SESSION STARTED: Admin '{actual_admin.email}' (ID: {actual_admin.id}) "
                f"started hijack session for '{target_user.email}' (ID: {target_user.id}) "
                f"from IP: {hijack_session.ip_address} | Session: {hijack_session.session_token}"
            )

            # Generate JWT tokens for the target user
            refresh = RefreshToken.for_user(target_user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response({
                'hijack_token': str(hijack_session.session_token),
                'access': access_token,
                'refresh': refresh_token,
                'user': UserSerializer(target_user).data,
                'admin_email': actual_admin.email,
                'expires_at': hijack_session.expires_at.isoformat()
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in StartHijackSessionView: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshHijackSessionView(APIView):
    """
    Refreshes a hijack session - extends expiry by another 15 minutes.
    POST /api/admin/hijack/refresh/
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOrHijacking]

    def post(self, request):
        try:
            hijack_token = request.headers.get('X-Hijack-Token') or request.data.get('hijack_token')

            if not hijack_token:
                return Response(
                    {'error': 'hijack_token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find and validate hijack session
            try:
                hijack_session = HijackSession.objects.get(
                    session_token=hijack_token,
                    is_active=True
                )
            except HijackSession.DoesNotExist:
                return Response(
                    {'error': 'Invalid or expired hijack session'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if session has expired
            if hijack_session.is_expired():
                hijack_session.end_session()
                return Response(
                    {'error': 'Hijack session has expired'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Refresh the expiry
            hijack_session.refresh_expiry()

            logger.info(
                f"HIJACK SESSION REFRESHED: Session {hijack_session.session_token} refreshed. "
                f"Admin '{hijack_session.admin_user.email}' viewing '{hijack_session.target_user.email}'. "
                f"New expiry: {hijack_session.expires_at}"
            )

            return Response({
                'expires_at': hijack_session.expires_at.isoformat(),
                'message': 'Session refreshed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in RefreshHijackSessionView: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EndHijackSessionView(APIView):
    """
    Ends a hijack session - returns admin to their own account.
    POST /api/admin/hijack/end/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            hijack_token = request.data.get('hijack_token')

            logger.info(f"EndHijackSessionView: Received request from user {request.user.email}")
            logger.info(f"EndHijackSessionView: Hijack token from body: {hijack_token}")

            if not hijack_token:
                logger.error("EndHijackSessionView: No hijack_token provided")
                return Response(
                    {'error': 'hijack_token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find and validate hijack session (skip IP/UA check for ending)
            try:
                hijack_session = HijackSession.objects.get(
                    session_token=hijack_token,
                    is_active=True
                )
                logger.info(
                    f"EndHijackSessionView: Found session - Admin: {hijack_session.admin_user.email}, "
                    f"Target: {hijack_session.target_user.email}"
                )
            except HijackSession.DoesNotExist:
                logger.error(f"EndHijackSessionView: Hijack session not found for token {hijack_token}")
                return Response(
                    {'error': 'Invalid or expired hijack session'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if session has expired
            if hijack_session.is_expired():
                logger.warning(f"EndHijackSessionView: Session {hijack_token} has expired")
                hijack_session.end_session()
                return Response(
                    {'error': 'Hijack session has expired'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # End the session
            admin_user = hijack_session.admin_user
            target_email = hijack_session.target_user.email
            hijack_session.end_session()

            logger.warning(
                f"HIJACK SESSION ENDED: Session {hijack_session.session_token} ended. "
                f"Admin '{admin_user.email}' returning from '{target_email}'"
            )

            # Generate fresh tokens for the admin user
            refresh = RefreshToken.for_user(admin_user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            admin_data = UserSerializer(admin_user).data
            logger.info(f"EndHijackSessionView: Returning admin user data: {admin_data}")

            return Response({
                'access': access_token,
                'refresh': refresh_token,
                'user': admin_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in EndHijackSessionView: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginAsUserView(APIView):
    """
    DEPRECATED: Use StartHijackSessionView instead.
    Kept for backward compatibility.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, user_id):
        # Redirect to new hijack session endpoint
        view = StartHijackSessionView.as_view()
        return view(request, user_id=user_id)


class ListUsersView(APIView):
    """
    Returns a list of all users for superadmin.
    GET /api/admin/users/
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOrHijacking]

    def get(self, request):
        try:
            users = User.objects.all().order_by('-date_joined')
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in ListUsersView: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
