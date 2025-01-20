from django.urls import path
from .views import (
    CustomDeleteAccountView,
    CustomEmailVerificationView,
    CustomPasswordChangeView,
    CustomPasswordResetConfirmView,
    CustomUserDetailsView,
)

app_name = "users"

urlpatterns = [
    # User management
    path("me/", CustomUserDetailsView.as_view(), name="user_details"),
    path("me/delete/", CustomDeleteAccountView.as_view(), name="account_delete"),
    
    # Password management
    path("password/change/", CustomPasswordChangeView.as_view(), name="password_change"),
    path("password/reset/confirm/<uidb64>/<token>/",
         CustomPasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    
    # Email verification
    path("verify-email/<str:key>/",
         CustomEmailVerificationView.as_view(),
         name="verify_email"),
]
