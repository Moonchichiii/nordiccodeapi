"""Contact serializer module for handling contact form data validation and serialization."""
from django.core.validators import EmailValidator
from rest_framework import serializers

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model with custom email validation.

    Attributes:
        email: EmailField with django's built-in email validator
    """

    email = serializers.EmailField(validators=[EmailValidator()])

    class Meta:
        """Meta class to specify model and fields for serialization."""
        model = Contact
        fields = ["id", "name", "email", "message", "created_at"]
