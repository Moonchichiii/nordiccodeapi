"""
Serializers for user-related operations including registration, authentication, and profile management.
"""

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import (
    PasswordResetSerializer,
    UserDetailsSerializer,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):
    """
    Enhanced registration serializer with additional user profile fields.
    Handles validation and custom signup logic for the extended user model.
    """

    full_name = serializers.CharField(
        required=False, allow_blank=True, max_length=150
    )
    phone_number = serializers.CharField(
        required=False, allow_blank=True, max_length=30
    )
    street_address = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    city = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    state_or_region = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    postal_code = serializers.CharField(
        required=False, allow_blank=True, max_length=20
    )
    country = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    vat_number = serializers.CharField(
        required=False, allow_blank=True, max_length=50
    )

    accepted_terms = serializers.BooleanField(required=True)
    marketing_consent = serializers.BooleanField(required=False, default=False)

    def validate_email(self, email):
        """Validate email uniqueness and format."""
        email = email.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "A user is already registered with this email address."
            )
        return email

    def validate(self, data):
        """Validate registration data including passwords and terms acceptance."""
        if data.get("password1") != data.get("password2"):
            raise serializers.ValidationError(
                {"password2": "Passwords must match."}
            )

        if not data.get("accepted_terms"):
            raise serializers.ValidationError(
                {"accepted_terms": "You must accept the terms of service."}
            )

        email = data.get("email", "").lower().strip()
        if email:
            self.validate_email(email)

        return data

    def get_cleaned_data(self):
        """Get cleaned data with additional profile fields."""
        cleaned_data = super().get_cleaned_data()
        profile_fields = {
            "full_name": "",
            "phone_number": "",
            "street_address": "",
            "city": "",
            "state_or_region": "",
            "postal_code": "",
            "country": "",
            "vat_number": "",
            "accepted_terms": False,
            "marketing_consent": False,
        }

        for field in profile_fields:
            profile_fields[field] = self.validated_data.get(
                field, profile_fields[field]
            )

        cleaned_data.update(profile_fields)
        return cleaned_data

    def custom_signup(self, request, user):
        """Handle custom signup logic for additional fields."""
        for field, value in self.cleaned_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    Serializer for retrieving and updating user details.
    Includes all custom profile fields as read-only.
    """

    full_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    street_address = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    state_or_region = serializers.CharField(read_only=True)
    postal_code = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    vat_number = serializers.CharField(read_only=True)
    accepted_terms = serializers.BooleanField(read_only=True)
    marketing_consent = serializers.BooleanField(read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        model = User
        fields = UserDetailsSerializer.Meta.fields + (
            "full_name",
            "phone_number",
            "street_address",
            "city",
            "state_or_region",
            "postal_code",
            "country",
            "vat_number",
            "accepted_terms",
            "marketing_consent",
        )
        read_only_fields = ("email",)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes additional user data in the response.
    """

    @classmethod
    def get_token(cls, user):
        """Generate token with any custom claims needed."""
        token = super().get_token(user)                
        return token

    def validate(self, attrs):
        """Validate credentials and return tokens with user data."""
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "full_name": self.user.full_name,
            "phone_number": self.user.phone_number,
            "street_address": self.user.street_address,
            "city": self.user.city,
            "state_or_region": self.user.state_or_region,
            "postal_code": self.user.postal_code,
            "country": self.user.country,
            "vat_number": self.user.vat_number,
            "accepted_terms": self.user.accepted_terms,
            "marketing_consent": self.user.marketing_consent,
        }

        return data


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """
    Serializer for password reset functionality with custom email template.
    """

    def get_email_options(self):
        """Configure email options for password reset."""
        return {
            "email_template_name": "password_reset_email.html",
            "extra_email_context": {
                "frontend_url": settings.PASSWORD_RESET_FRONTEND_URL
            },
        }
