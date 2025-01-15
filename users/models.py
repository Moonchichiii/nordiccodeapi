"""
Core user models for the application.
Provides a custom user model with email authentication and extended profile fields.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.

        Args:
            email (str): User's email address.
            password (str, optional): User's password.
            **extra_fields: Additional fields for the user model.

        Returns:
            CustomUser: The created user object.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError("Users must provide an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.

        Args:
            email (str): Superuser's email address.
            password (str, optional): Superuser's password.
            **extra_fields: Additional fields for the user model.

        Returns:
            CustomUser: The created superuser object.

        Raises:
            ValueError: If required superuser flags are not True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email for authentication and includes
    additional profile and business-related fields.
    """

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message=(
            "Phone number must be in format: '+999999999'. "
            "Up to 15 digits."
        ),
    )

    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )
    is_verified = models.BooleanField(
        "email verified",
        default=False,
        help_text="Designates whether this user has verified their email address.",
    )
    full_name = models.CharField(
        "full name", max_length=150, blank=True
    )
    phone_number = models.CharField(
        "phone number",
        max_length=30,
        validators=[phone_regex],
        blank=True,
    )
    street_address = models.CharField(
        "street address", max_length=255, blank=True
    )
    city = models.CharField("city", max_length=100, blank=True)
    state_or_region = models.CharField(
        "state/region", max_length=100, blank=True
    )
    postal_code = models.CharField(
        "postal code", max_length=20, blank=True
    )
    country = models.CharField(
        "country", max_length=100, blank=True
    )
    vat_number = models.CharField(
        "VAT number", max_length=50, blank=True
    )
    accepted_terms = models.BooleanField(
        "accepted terms",
        default=False,
        help_text=(
            "Designates whether the user has accepted the Terms of Service."
        ),
    )
    marketing_consent = models.BooleanField(
        "marketing consent",
        default=False,
        help_text=(
            "Designates whether the user has consented to marketing "
            "communications."
        ),
    )
    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text=(
            "Designates whether the user can log into the admin site."
        ),
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text=(
            "Designates whether this user account should be considered active."
        ),
    )
    date_joined = models.DateTimeField(
        "date joined", default=timezone.now
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-date_joined"]

    def __str__(self):
        """Return the user's email as string representation."""
        return self.email

    def clean(self):
        """Clean the model fields before saving."""
        super().clean()
        self.email = self.email.lower().strip()

    def save(self, *args, **kwargs):
        """Ensure model cleaning is performed on save."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_email_verified(self):
        """
        Property for compatibility with django-allauth.
        Returns whether the user's email is verified.
        """
        return self.is_verified

    def get_full_name(self):
        """Return the user's full name or email if no name is set."""
        return self.full_name.strip() if self.full_name else self.email

    def get_short_name(self):
        """Return the first part of the user's full name or the email if none."""
        name_parts = self.full_name.split()
        return name_parts[0] if name_parts else self.email
