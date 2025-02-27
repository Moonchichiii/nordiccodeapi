from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CustomUser

logger = logging.getLogger(__name__)

class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser model."""

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        try:
            validate_email(email)
            return True
        except ValidationError as e:
            logger.debug(f"Email validation failed for {email}: {e}")
            return False

    def _create_user(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """
        Create and save a user with the given email and password.
        
        If no password is provided, set an unusable password.
        """
        if not email:
            raise ValueError("A valid email address is required")

        email = self.normalize_email(email).lower()

        if not self.validate_email(email):
            raise ValueError("Invalid email format")

        user = self.model(email=email, **extra_fields)
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """Create a standard user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """Create a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email: str) -> 'CustomUser':
        """Allow lookup by email (case-insensitive)."""
        return self.get(email__iexact=email)
