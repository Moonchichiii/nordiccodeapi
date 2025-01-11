"""
URL configuration for the backend application.
"""

from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from allauth.account.views import confirm_email
from dj_rest_auth.registration.views import (
    RegisterView,
    ResendEmailVerificationView,
    VerifyEmailView,
)
from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from users.views import CustomTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/contacts/", include("contacts.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/chatbot/", include("chatbot.urls")),
    path("auth/login/", LoginView.as_view(), name="rest_login"),
    path("auth/logout/", LogoutView.as_view(), name="rest_logout"),
    path(
        "auth/password/change/",
        PasswordChangeView.as_view(),
        name="rest_password_change",
    ),
    path(
        "auth/password/reset/",
        PasswordResetView.as_view(),
        name="rest_password_reset",
    ),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    path("auth/registration/", RegisterView.as_view(), name="rest_register"),
    path(
        "auth/registration/verify-email/",
        VerifyEmailView.as_view(),
        name="rest_verify_email",
    ),
    path(
        "auth/registration/resend-verification/",
        ResendEmailVerificationView.as_view(),
        name="rest_resend_email",
    ),
    path(
        "auth/registration/verification-sent/",
        TemplateView.as_view(template_name="account/email_verification_sent.html"),
        name="account_email_verification_sent",
    ),
    re_path(
        r"^accounts/confirm-email/(?P<key>[-:\w]+)/$",
        confirm_email,
        name="account_confirm_email",
    ),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
