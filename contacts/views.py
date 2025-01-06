"""Views module for managing contact-related operations in the application.

This module provides ViewSet implementations for handling contact messages,
including creation and listing operations with rate limiting.
"""

import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, viewsets

from .models import Contact
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contact messages.

    Provides CRUD operations for Contact model with rate limiting on creation.

    Attributes:
        queryset: QuerySet of all Contact objects
        serializer_class: Serializer class for Contact model
        permission_classes: List of permission classes applied to the viewset
    """

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def create(self, request, *args, **kwargs):
        """Create a new contact message.

        Rate-limited to 5 requests per minute per IP address.
        Email notifications are handled through model signals.

        Args:
            request: The HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            Response object with the created contact data
        """
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Save the contact message to the database.

        Args:
            serializer: Validated serializer instance containing contact data
        """
        serializer.save()
