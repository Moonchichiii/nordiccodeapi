import logging

from allauth.account.views import ConfirmEmailView
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import CustomTokenObtainPairSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens with additional user data.
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to obtain JWT tokens.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user

            if not user.is_verified:
                raise AuthenticationFailed("Email address is not verified.")

            data = serializer.validated_data
            access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
            refresh_lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
            data["access_expiration"] = (timezone.now() + access_lifetime).isoformat()
            data["refresh_expiration"] = (timezone.now() + refresh_lifetime).isoformat()

            return Response(data)

        except AuthenticationFailed as e:
            logger.warning("Authentication failed: %s", str(e))
            raise
        except TokenError as e:
            logger.error("Token error: %s", str(e))
            raise AuthenticationFailed("Authentication failed.")


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view for refreshing JWT tokens.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to refresh JWT tokens.
        """
        refresh_token = request.data.get("refresh", "")
        if not refresh_token:
            logger.warning("Refresh token is missing.")
            raise TokenError("Refresh token is required")

        try:
            logger.debug("Processing token refresh request")
            response = super().post(request, *args, **kwargs)
            access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
            response.data["access_expiration"] = (timezone.now() + access_lifetime).isoformat()
            return response

        except TokenError as e:
            logger.warning("Token refresh error: %s", str(e))
            raise InvalidToken(str(e))


class CustomConfirmEmailView(ConfirmEmailView):
    """
    Custom view for confirming email addresses.
    """

    def post(self, *args, **kwargs):
        """
        Handle POST request to confirm email.
        """
        try:
            self.object = self.get_object()
            self.object.confirm(self.request)
            user = self.object.email_address.user

            if not user.is_active:
                logger.warning("Inactive user attempted to confirm email: %s", user.email)
                return redirect(settings.ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL)

            login(self.request, user)
            refresh = RefreshToken.for_user(user)

            response = redirect(settings.ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL)
            response.set_cookie(
                "access_token",
                str(refresh.access_token),
                httponly=True,
                samesite="Lax",
                secure=not settings.DEBUG,
                max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            )
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                samesite="Lax",
                secure=not settings.DEBUG,
                max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            )

            return response

        except TokenError as e:
            logger.error("Token error during email confirmation: %s", str(e))
            return redirect(settings.ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL)
        except Exception as e:
            logger.error("Error during email confirmation: %s", str(e))
            return redirect(settings.ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL)


def email_verification_sent(request):
    """
    Render the email verification sent page.
    """
    return render(request, "templates/email_verification_sent.html")
