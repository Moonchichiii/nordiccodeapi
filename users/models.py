from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with additional fields.
    """
    email = models.EmailField(
        "email address",
        unique=True,
        db_index=True,
        error_messages={"unique": "A user with that email already exists"},
    )
    is_verified = models.BooleanField("email verified", default=False, db_index=True)
    full_name = models.CharField(
        "full name",
        max_length=150,
        blank=False,
        validators=[RegexValidator(r"^[a-zA-Z\s]{2,}$")],
    )
    phone_number = models.CharField(
        "phone number",
        max_length=30,
        blank=False,
        validators=[RegexValidator(r"^\+?1?\d{9,15}$")],
    )
    street_address = models.CharField("street address", max_length=255, blank=False)
    city = models.CharField("city", max_length=100, blank=False)
    postal_code = models.CharField("postal code", max_length=20, blank=False)
    country = models.CharField("country", max_length=100, blank=False)
    state_or_region = models.CharField("state/region", max_length=100, blank=True)
    vat_number = models.CharField("VAT number", max_length=50, blank=True)
    accepted_terms = models.BooleanField("accepted terms", default=False, db_index=True)
    marketing_consent = models.BooleanField("marketing consent", default=False)
    is_staff = models.BooleanField("staff status", default=False)
    is_active = models.BooleanField("active", default=True)
    date_joined = models.DateTimeField("date joined", default=timezone.now)

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone_number"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [
            models.Index(fields=["email", "is_verified"]),
            models.Index(fields=["is_staff", "is_active"]),
        ]

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        if self.full_name:
            return self.full_name.split()[0]
        return ""
