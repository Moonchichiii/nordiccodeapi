from django.urls import path

from .views import (
    AccountDeletionView,
    EmailVerificationView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    ResendVerificationEmailView,
    UserDetailsView,
)

app_name = "users"

urlpatterns = [
   # Auth
   path("login/", LoginView.as_view(), name="login"),
   path("logout/", LogoutView.as_view(), name="logout"),
   
   # Email verification
   path("verify-email/<str:key>/", EmailVerificationView.as_view(), name="verify_email"),
   path("resend-verification/", ResendVerificationEmailView.as_view(), name="resend_verification"),
   
   # User management
   path("me/", UserDetailsView.as_view(), name="user_details"),
   path("me/delete/", AccountDeletionView.as_view(), name="delete_account"),
   
   # Password management  
   path("password/change/", PasswordChangeView.as_view(), name="password_change"),
   path("password/reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset"),
]