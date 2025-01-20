from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class CaseInsensitiveEmailBackend(ModelBackend):
    """Authenticate using case-insensitive email lookup."""

    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        """
        Authenticate a user based on email (case-insensitive) and password.
        """
        UserModel = get_user_model()

        email = (username or email or "").lower().strip()
        if not email or not password:
            return None

        try:
            user = UserModel.objects.get(email__iexact=email)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            return None

        return None
