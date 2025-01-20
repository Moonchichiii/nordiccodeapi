import logging
from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from .serializers import CustomUserDetailsSerializer
from .tokenservice import TokenService

User = get_user_model()
logger = logging.getLogger(__name__)

def api_error_response(message, code="error", status_code=400, extra_data=None):
    """Return a standardized error response."""
    response_data = {
        "detail": message,
        "code": code,
        "success": False
    }
    if extra_data:
        response_data.update(extra_data)
    return Response(response_data, status=status_code)

class CustomEmailVerificationView(APIView):
    """Handle email verification and set JWT tokens in cookies."""
    authentication_classes = []
    permission_classes = []

    def get_tokens_for_user(self, user):
        """Generate secure JWT tokens for the verified user."""
        return TokenService.get_tokens_for_user(user)

    def get(self, request, key):
        """Verify email using the provided key."""
        try:
            confirmation = EmailConfirmationHMAC.from_key(key) or EmailConfirmation.objects.get(key=key)
            if confirmation.has_expired():
                logger.warning(f"Expired verification link for user: {confirmation.email_address.email}")
                return redirect(f"{settings.FRONTEND_URL}/email-verification-failed?error=expired")

            confirmation.confirm(request)
            confirmation.delete()

            user = confirmation.email_address.user
            user.is_verified = True
            user.save()

            tokens = self.get_tokens_for_user(user)

            response = redirect(f"{settings.FRONTEND_URL}/email-verified")
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                tokens['access'],
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
            )
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                tokens['refresh'],
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
            )

            logger.info(f"Email successfully verified for user: {user.email}")
            return response

        except (EmailConfirmation.DoesNotExist, TypeError, ValueError) as e:
            logger.error(f"Email verification failed: {str(e)}")
            return redirect(f"{settings.FRONTEND_URL}/email-verification-failed?error=invalid")

class ResendVerificationEmailView(APIView):
    """Resend the email confirmation link."""
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return api_error_response("Email is required")

        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return api_error_response("Email already verified")

            from allauth.account.utils import send_email_confirmation
            send_email_confirmation(request, user)

            return Response({"detail": "Verification email sent"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return api_error_response("User not found", code="not_found", status_code=404)

class CustomUserDetailsView(APIView):
    """Retrieve and update comprehensive user details."""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserDetailsSerializer

    def get(self, request):
        """Retrieve the user's profile details."""
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update the user's profile details."""
        serializer = self.serializer_class(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return api_error_response(
            message="Invalid data provided.",
            extra_data={"errors": serializer.errors}
        )

class CustomPasswordChangeView(APIView):
    """Change the user's password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return api_error_response("Both old and new passwords are required")

        if not request.user.check_password(old_password):
            return api_error_response("Current password is incorrect")

        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            return api_error_response("Password validation failed", extra_data={"errors": list(e.messages)})

        request.user.set_password(new_password)
        request.user.save()

        logger.info(f"Password changed for user: {request.user.email}")
        return Response({"detail": "Password successfully changed", "success": True})

class CustomPasswordResetConfirmView(APIView):
    """Reset password using a valid UID and token."""
    def get_user(self, uidb64):
        """Retrieve user by UID."""
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def validate_token(self, user, token):
        """Validate the reset token."""
        return user is not None and default_token_generator.check_token(user, token)

    def post(self, request, uidb64, token):
        """Reset the user's password."""
        user = self.get_user(uidb64)

        if not user or not self.validate_token(user, token):
            return api_error_response("Invalid or expired reset token", code="invalid_token")

        new_password = request.data.get("new_password")
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return api_error_response("Password validation failed", extra_data={"errors": list(e.messages)})

        user.set_password(new_password)
        user.save()

        logger.info(f"Password reset for user: {user.email}")
        return Response({"detail": "Password successfully reset", "success": True})

class CustomDeleteAccountView(APIView):
    """Delete the currently authenticated user's account."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Delete the user's account."""
        try:
            request.user.delete()
            logger.info(f"Account deleted for user: {request.user.email}")
            return Response({"detail": "Account successfully deleted", "success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to delete account for user: {request.user.email} - {str(e)}")
            return api_error_response("Failed to delete account", code="deletion_failed", status_code=500)
