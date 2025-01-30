import logging
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Project, ProjectPackage
from .serializers import ProjectPackageSerializer, ProjectSerializer

logger = logging.getLogger(__name__)


class ProjectPackageViewSet(viewsets.ModelViewSet):
    """Manage Project Packages."""

    queryset = ProjectPackage.objects.all()
    serializer_class = ProjectPackageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self) -> list:
        """Assign permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer: ProjectPackageSerializer) -> None:
        """Create a new project package."""
        try:
            with transaction.atomic():
                project_package = serializer.save()
                logger.info(
                    f"Creating new project package by {self.request.user.email}"
                )
                logger.info(f"Successfully created package: {project_package.name}")
        except ValidationError as e:
            logger.error(f"Validation error creating package: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating package: {str(e)}")
            raise

    def perform_update(self, serializer: ProjectPackageSerializer) -> None:
        """Update an existing project package."""
        try:
            with transaction.atomic():
                project_package = serializer.save()
                logger.info(
                    f"Updating package {project_package.id} by {self.request.user.email}"
                )
                logger.info(f"Successfully updated package {project_package.id}")
        except ObjectDoesNotExist:
            logger.error(f"Package not found: {self.kwargs.get('pk')}")
            raise ValidationError(_("Package not found"))
        except Exception as e:
            logger.error(f"Error updating package: {str(e)}")
            raise


class ProjectViewSet(viewsets.ModelViewSet):
    """Manage Projects."""

    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "status": ["exact"],
        "package__name": ["exact"],
    }
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self) -> Any:
        """Return projects for the current authenticated user."""
        return Project.objects.select_related("user", "package").filter(
            user=self.request.user
        )

    def perform_create(self, serializer: ProjectSerializer) -> None:
        """Create a new project."""
        try:
            with transaction.atomic():
                project = serializer.save(user=self.request.user)
                logger.info(
                    f"Project '{project.title}' created by {self.request.user.email}"
                )
        except ValidationError as e:
            logger.error(f"Validation error creating project: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating project: {str(e)}")
            raise

    def perform_update(self, serializer: ProjectSerializer) -> None:
        """Update an existing project."""
        try:
            with transaction.atomic():
                instance = serializer.instance
                new_status = serializer.validated_data.get("status")

                if new_status == Project.StatusChoices.COMPLETED:
                    if not instance.assigned_staff.exists():
                        raise ValidationError(
                            {
                                "status": "Cannot mark as completed without assigned staff"
                            }
                        )

                project = serializer.save()
                logger.info(f"Project {project.id} updated - Status: {project.status}")
        except ValidationError as e:
            logger.error(f"Validation error updating project: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            raise

    def update(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """Override the default update method."""
        try:
            instance = self.get_object()
            logger.info(f"Updating project {instance.id} by {request.user.email}")

            if instance.user != request.user:
                logger.warning(
                    f"User {request.user.email} attempted to update project "
                    f"{instance.id} owned by {instance.user.email}"
                )
                raise PermissionDenied(
                    _("You don't have permission to update this project")
                )

            return super().update(request, *args, **kwargs)

        except ObjectDoesNotExist:
            logger.error(f"Project not found: {kwargs.get('pk')}")
            return Response(
                {"error": _("Project not found")}, status=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            logger.error(f"Validation error updating project: {str(e)}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            return Response(
                {"error": _("Failed to update project")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
