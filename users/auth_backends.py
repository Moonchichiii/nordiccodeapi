"""
Authentication backend for case-insensitive email login.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class CaseInsensitiveEmailBackend(ModelBackend):
    """Authenticate using case-insensitive email lookup."""

    def authenticate(
        self, request, username=None, email=None, password=None, **kwargs
    ):
        """
        Authenticate using either username or email, normalized to lowercase.
        """
        username = username or email

        if not username or not password:
            return None

        normalized_email = username.strip().lower()

        try:
            user = UserModel.objects.get(email=normalized_email)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
