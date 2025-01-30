import logging

from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser as User
from .serializers import CustomLoginSerializer, CustomUserDetailsSerializer
from .services import EmailService, SecurityService, TokenService

logger = logging.getLogger(__name__)


class EmailVerificationView(APIView):
    """Verify email address."""
    permission_classes = []

    def get(self, request, key):
        try:
            confirmation = (EmailConfirmationHMAC.from_key(key) or
                            EmailConfirmation.objects.get(key=key))
            if confirmation.has_expired():
                return redirect(
                    f"{settings.FRONTEND_URL}/email-verification-failed?error=expired"
                )

            user = confirmation.email_address.user
            user.is_verified = True
            user.save()

            tokens = TokenService.get_tokens_for_user(user)
            response = redirect(f"{settings.FRONTEND_URL}/email-verified")
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                tokens['access'],
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
            )
            SecurityService.log_security_event('email_verified', {'user_id': user.id})
            return response

        except (EmailConfirmation.DoesNotExist, TypeError, ValueError):
            return redirect(f"{settings.FRONTEND_URL}/email-verification-failed")


class ResendVerificationEmailView(APIView):
    """Resend verification email."""

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({"detail": "Already verified"},
                                status=status.HTTP_400_BAD_REQUEST)

            EmailService.send_activation_email(user, request.build_absolute_uri('/'))
            return Response({"detail": "Email sent"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)


class UserDetailsView(APIView):
    """Retrieve or update user details."""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserDetailsSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """Change user password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "Both passwords required"},
                            status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
            return Response({"detail": "Incorrect password"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, request.user)
            request.user.set_password(new_password)
            request.user.save()
            SecurityService.log_security_event('password_changed',
                                               {'user_id': request.user.id})
            return Response({"detail": "Password updated"})
        except ValidationError as e:
            return Response({"detail": e.messages},
                            status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm password reset."""

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            return Response({"detail": "Invalid reset link"},
                            status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid/expired token"},
                            status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get("new_password")
        try:
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            SecurityService.log_security_event('password_reset',
                                               {'user_id': user.id})
            return Response({"detail": "Password reset successful"})
        except ValidationError as e:
            return Response({"detail": e.messages},
                            status=status.HTTP_400_BAD_REQUEST)


class AccountDeletionView(APIView):
    """Delete user account."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            user_id = request.user.id
            request.user.delete()
            SecurityService.log_security_event('account_deleted',
                                               {'user_id': user_id})
            return Response({"detail": "Account deleted"},
                            status=status.HTTP_200_OK)
        except Exception as e:
            SecurityService.log_security_event('account_deletion_failed', {
                'user_id': request.user.id,
                'error': str(e)
            })
            return Response({"detail": "Deletion failed"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """User login."""

    def post(self, request):
        serializer = CustomLoginSerializer(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            if not SecurityService.check_login_attempts(user.email):
                return Response({"detail": "Account locked"},
                                status=status.HTTP_403_FORBIDDEN)

            tokens = TokenService.get_tokens_for_user(user)
            SecurityService.log_security_event('login_success',
                                               {'user_id': user.id})
            response = Response({"detail": "Login successful", "tokens": tokens})

            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                tokens['access'],
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
            )
            return response

        SecurityService.log_security_event('login_failed',
                                           {'email': request.data.get('email')})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """User logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            TokenService.revoke_user_tokens(request.user)
            response = Response({"detail": "Logged out"})
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            SecurityService.log_security_event('logout',
                                               {'user_id': request.user.id})
            return response
        except Exception:
            return Response({"detail": "Logout failed"},
                            status=status.HTTP_400_BAD_REQUEST)