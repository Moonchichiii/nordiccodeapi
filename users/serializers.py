import re

from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import CustomUser
from .services import AddressService


class CustomRegisterSerializer(RegisterSerializer):
    """Serializer for user registration with custom fields."""
    full_name = serializers.CharField(
        max_length=150,
        required=True,
        validators=[RegexValidator(r"^[a-zA-Z\s]{2,}$")]
    )
    phone_number = serializers.CharField(
        required=True,
        validators=[RegexValidator(r"^\+?1?\d{9,15}$")]
    )
    street_address = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    accepted_terms = serializers.BooleanField(required=True)
    marketing_consent = serializers.BooleanField(default=False, required=False)

    def validate(self, data: dict) -> dict:
        """Validate registration data."""
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(
                {"password2": "Passwords don't match"}
            )

        if not data.get("accepted_terms"):
            raise serializers.ValidationError(
                {"accepted_terms": "Terms must be accepted"}
            )

        address_valid = AddressService.validate_address(
            data.get("street_address"),
            data.get("postal_code"),
            data.get("city"),
            data.get("country")
        )
        if not address_valid["is_valid"]:
            raise serializers.ValidationError({"address": "Invalid address"})

        return data

    def save(self, request) -> CustomUser:
        """Save the new user."""
        validated_data = {**self.validated_data}
        validated_data.pop("password2", None)
        password = validated_data.pop("password1")

        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomLoginSerializer(LoginSerializer):
    """Serializer for user login with email and password."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        """Validate login credentials."""
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError(
                'Both email and password required'
            )

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_verified:
            raise serializers.ValidationError("Please verify your email first")

        attrs["user"] = user
        return attrs


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """Serializer for user details with additional fields."""
    class Meta(UserDetailsSerializer.Meta):
        model = CustomUser
        fields = UserDetailsSerializer.Meta.fields + (
            "full_name", "phone_number", "street_address", "city",
            "state_or_region", "postal_code", "country", "vat_number",
            "accepted_terms", "marketing_consent", "is_verified",
        )
        read_only_fields = ("email", "is_verified", "accepted_terms")

    def validate(self, data: dict) -> dict:
        """Validate user details."""
        address_fields = ["street_address", "city", "postal_code", "country"]
        if any(field in data for field in address_fields):
            address_valid = AddressService.validate_address(
                data.get("street_address"),
                data.get("postal_code"),
                data.get("city"),
                data.get("country")
            )
            if not address_valid["is_valid"]:
                raise serializers.ValidationError({"address": "Invalid address"})
        return data
