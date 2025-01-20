from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from rest_framework import serializers

from .address_validation import AddressValidationService
from .models import CustomUser


class CustomRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(
        max_length=150,
        required=True,
        validators=[
            RegexValidator(
                r"^[a-zA-Z\s]{2,}$",
                "Full name must contain at least two alphabetic characters",
            )
        ],
    )
    phone_number = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                r"^\+?1?\d{9,15}$",
                "Phone number must be in international format: '+999999999'",
            )
        ],
    )
    street_address = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    accepted_terms = serializers.BooleanField(
        required=True,
        error_messages={"required": "You must accept the Terms of Service"},
    )
    marketing_consent = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "password1",
            "password2",
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

    def validate(self, data):
        """Validate registration data."""
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match"})

        if not data.get("accepted_terms"):
            raise serializers.ValidationError(
                {"accepted_terms": "Terms must be accepted"}
            )

        address_valid = AddressValidationService.validate_address(
            data.get("street_address"),
            data.get("postal_code"),
            data.get("city"),
            data.get("country"),
        )
        if not address_valid["is_valid"]:
            raise serializers.ValidationError({"address": "Invalid address"})

        return data

    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop("password2")
        password = validated_data.pop("password1")
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomLoginSerializer(LoginSerializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError('Must include "email" and "password"')

        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )

        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials"
            )

        if not user.is_verified:
            raise serializers.ValidationError(
                "Email not verified. Please verify your email first."
            )

        attrs["user"] = user
        return attrs


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """Serializer for user details."""

    class Meta(UserDetailsSerializer.Meta):
        model = CustomUser
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
            "is_verified",
        )
        read_only_fields = ("email", "is_verified", "accepted_terms")

    def validate_phone_number(self, value):
        """Validate phone number format."""
        if not RegexValidator(r"^\+?1?\d{9,15}$")(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value

    def validate(self, data):
        """Validate user details."""
        address_fields = ["street_address", "city", "postal_code", "country"]
        if any(field in data for field in address_fields):
            address_valid = AddressValidationService.validate_address(
                data.get("street_address"),
                data.get("postal_code"),
                data.get("city"),
                data.get("country"),
            )
            if not address_valid["is_valid"]:
                raise serializers.ValidationError({"address": "Invalid address"})
        return data
