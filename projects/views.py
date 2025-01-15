"""
Views for managing projects and project packages.
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Project, ProjectPackage
from .serializers import ProjectSerializer, ProjectPackageSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class ProjectPackageViewSet(viewsets.ReadOnlyModelViewSet):
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Project.objects.select_related("user", "package").filter(
            user=self.request.user
        )


class ProjectPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for ProjectPackage.
    """

    queryset = ProjectPackage.objects.all()
    serializer_class = ProjectPackageSerializer
    permission_classes = [AllowAny]
