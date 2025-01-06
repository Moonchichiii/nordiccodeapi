"""
Views for handling project order operations in the Nordic Code API.

This module provides ViewSets for managing project orders with proper user authentication
and filtering capabilities.
"""

from rest_framework import permissions
from rest_framework import viewsets

from .models import ProjectOrder
from .serializers import ProjectOrderSerializer


class ProjectOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project order operations.

    Provides CRUD operations for ProjectOrder instances with user-based filtering
    and automatic user assignment on creation.

    Attributes:
        queryset: QuerySet of all ProjectOrder objects
        serializer_class: Serializer class for ProjectOrder model
        permission_classes: List of permission classes required for access
    """

    queryset = ProjectOrder.objects.all()
    serializer_class = ProjectOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer) -> None:
        """
        Create a new project order associated with the current user.

        Args:
            serializer: The serializer instance containing validated data
        """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Filter orders to show only those belonging to the current user.

        Returns:
            QuerySet: Filtered queryset containing user's project orders
        """
        return self.queryset.filter(user=self.request.user)
