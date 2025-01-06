"""Views for handling JWT token authentication with cookies."""

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        tokens = RefreshToken.for_user(request.user)

        # Set tokens in HttpOnly cookies
        response.set_cookie(
            "access_token",
            str(tokens.access_token),
            httponly=True,
            samesite="Lax",
        )
        response.set_cookie(
            "refresh_token",
            str(tokens),
            httponly=True,
            samesite="Lax",
        )
        return response
