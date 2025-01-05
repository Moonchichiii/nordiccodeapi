"""Views for handling project order operations."""

from rest_framework import permissions, viewsets

from .models import ProjectOrder
from .serializers import ProjectOrderSerializer


class ProjectOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing project orders."""

    queryset = ProjectOrder.objects.all()
    serializer_class = ProjectOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically associate the order with the current user
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Limit visible orders to the currently authenticated user
        return self.queryset.filter(user=self.request.user)
