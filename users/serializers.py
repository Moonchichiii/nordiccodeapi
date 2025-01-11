"""
Serializers for user-related operations.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import PasswordResetSerializer, UserDetailsSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):
    """
    Serializer for user registration with additional fields.
    """
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    street_address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state_or_region = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    vat_number = serializers.CharField(required=False, allow_blank=True)
    accepted_terms = serializers.BooleanField(required=True)
    marketing_consent = serializers.BooleanField(required=False, default=False)

    def validate_email(self, email):
        """
        Validate that the email is unique.
        """
        email = email.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "A user is already registered with this email address."
            )
        return email

    def validate(self, data):
        """
        Validate the registration data.
        """
        if data.get("password1") != data.get("password2"):
            raise serializers.ValidationError({"password2": "Passwords must match."})
        if not data.get("accepted_terms"):
            raise serializers.ValidationError(
                {"accepted_terms": "You must accept the terms."}
            )

        email = data.get("email", "").lower().strip()
        if email:
            self.validate_email(email)

        return data

    def get_cleaned_data(self):
        """
        Get cleaned data for user creation.
        """
        cleaned_data = super().get_cleaned_data()
        cleaned_data.update(
            {
                "full_name": self.validated_data.get("full_name", ""),
                "phone_number": self.validated_data.get("phone_number", ""),
                "street_address": self.validated_data.get("street_address", ""),
                "city": self.validated_data.get("city", ""),
                "state_or_region": self.validated_data.get("state_or_region", ""),
                "postal_code": self.validated_data.get("postal_code", ""),
                "country": self.validated_data.get("country", ""),
                "vat_number": self.validated_data.get("vat_number", ""),
                "accepted_terms": self.validated_data.get("accepted_terms", False),
                "marketing_consent": self.validated_data.get(
                    "marketing_consent", False
                ),
            }
        )
        return cleaned_data

    def custom_signup(self, request, user):
        """
        Custom signup logic to save additional user fields.
        """
        user.full_name = self.cleaned_data.get("full_name", "")
        user.phone_number = self.cleaned_data.get("phone_number", "")
        user.street_address = self.cleaned_data.get("street_address", "")
        user.city = self.cleaned_data.get("city", "")
        user.state_or_region = self.cleaned_data.get("state_or_region", "")
        user.postal_code = self.cleaned_data.get("postal_code", "")
        user.country = self.cleaned_data.get("country", "")
        user.vat_number = self.cleaned_data.get("vat_number", "")
        user.accepted_terms = self.cleaned_data.get("accepted_terms", False)
        user.marketing_consent = self.cleaned_data.get("marketing_consent", False)
        user.save()


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    Serializer for user details with additional read-only fields.
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
    Serializer for obtaining JWT tokens with additional user data.
    """
    def validate(self, attrs):
        """
        Validate and return token with additional user data.
        """
        data = super().validate(attrs)
        user = self.user
        data.update(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone_number": user.phone_number,
                    "street_address": user.street_address,
                    "city": user.city,
                    "state_or_region": user.state_or_region,
                    "postal_code": user.postal_code,
                    "country": user.country,
                    "vat_number": user.vat_number,
                    "accepted_terms": user.accepted_terms,
                    "marketing_consent": user.marketing_consent,
                }
            }
        )
        return data


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """
    Serializer for password reset with custom email options.
    """
    def get_email_options(self):
        """
        Get email options for password reset email.
        """
        return {
            "email_template_name": "password_reset_email.html",
            "extra_email_context": {
                "frontend_url": "http://localhost:5173/reset-password"
            },
        }
