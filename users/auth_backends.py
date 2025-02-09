from typing import Optional
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveEmailBackend(ModelBackend):
    """Authenticate using case-insensitive email lookup."""

    def authenticate(
        self,
        request,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> Optional[get_user_model()]:
        """
        Authenticate a user based solely on email (case-insensitive) and password.

        Args:
            request: The HTTP request object.
            email: The email of the user.
            password: The password of the user.

        Returns:
            The authenticated user if credentials are valid, otherwise None.
        """
        UserModel = get_user_model()

        email = (email or "").lower().strip()
        if not email or not password:
            return None

        try:
            user = UserModel.objects.get(email__iexact=email)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            return None

        return None
