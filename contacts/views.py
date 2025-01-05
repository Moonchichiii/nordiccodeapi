"""
Views for the contacts application.
"""

import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, viewsets

from .models import Contact
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)


class ContactViewSet(viewsets.ModelViewSet):
    """
    A viewset for creating and listing contact messages.
    """

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def create(self, request, *args, **kwargs):
        """
        Create a new contact. Rate-limited to 5 requests/minute per IP.
        Email sending will be handled by signals.
        """
        response = super().create(request, *args, **kwargs)
        return response

    def perform_create(self, serializer):
        """
        Save the contact in the database.
        Email sending will be handled by signals.
        """
        serializer.save()
