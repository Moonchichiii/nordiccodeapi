from allauth.account.views import ConfirmEmailView
from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    


User = get_user_model()

# For production only! 
# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer

#     def post(self, request, *args, **kwargs):

#         email = request.data.get("email")
#         password = request.data.get("password")

#         try:

#             user = User.objects.get(email=email)
#         except User.DoesNotExist:
#             raise AuthenticationFailed("No user found with this email.")


#         if not user.is_verified:
#             raise AuthenticationFailed("Email address is not verified.")


#         if not user.check_password(password):
#             raise AuthenticationFailed("Invalid credentials.")


#         refresh = RefreshToken.for_user(user)


#         return Response(
#             {
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "full_name": user.full_name,
#                 },
#             }
#         )



class CustomConfirmEmailView(ConfirmEmailView):
    def post(self, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.confirm(self.request)
            user = self.object.email_address.user

            if user.is_active:
                login(self.request, user)
                refresh = RefreshToken.for_user(user)

                frontend_url = (
                    settings.ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL
                )
                response = redirect(frontend_url)
                response.set_cookie(
                    "access_token",
                    str(refresh.access_token),
                    httponly=True,
                    samesite="Lax",
                    secure=not settings.DEBUG,
                )
                response.set_cookie(
                    "refresh_token",
                    str(refresh),
                    httponly=True,
                    samesite="Lax",
                    secure=not settings.DEBUG,
                )
                return response

            return redirect(settings.ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL)
        except Exception as e:
            logger.error(f"Error during email confirmation: {e}")
            return redirect(settings.ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL)


def email_verification_sent(request):
    return render(request, "templates/email_verification_sent.html", {})
