"""URL configurations for user operations."""

from django.urls import path, re_path

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomConfirmEmailView,
)

urlpatterns = [
    path(
        "token/",
        CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    re_path(
        r"^confirm-email/(?P<key>[-:\w]+)/$",
        CustomConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
]
