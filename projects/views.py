# projects/views.py
from django.db.models import Prefetch
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ProjectPackage, Addon, Project, ProjectAddon
from .serializers import (
    ProjectPackageSerializer,
    AddonSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer
)
from planner.models import PlannerSubmission

class ProjectPackageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProjectPackage.objects.filter(is_active=True)
    serializer_class = ProjectPackageSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def compatible_addons(self, request, pk=None):
        package = self.get_object()
        addons = package.compatible_addons.filter(is_active=True)
        serializer = AddonSerializer(addons, many=True)
        return Response(serializer.data)

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).prefetch_related(
            'package',
            Prefetch(
                'projectaddon_set',
                queryset=ProjectAddon.objects.select_related('addon')
            )
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        # Create the project as a draft then set its status to planning.
        project = serializer.save(user=self.request.user, status='draft')
        project.status = 'planning'
        project.save()

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def approve_planning(self, request, pk=None):
        project = self.get_object()
        if project.status != 'planning':
            return Response({'error': 'Project must be in planning phase.'},
                            status=status.HTTP_400_BAD_REQUEST)
        project.approve_planning()
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def lock_planning(self, request, pk=None):
        project = self.get_object()
        if project.status != 'planning':
            return Response({'error': 'Project must be in planning phase.'},
                            status=status.HTTP_400_BAD_REQUEST)
        project.is_planning_locked = True
        project.save()
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_planning(self, request, pk=None):
        project = self.get_object()
        if project.is_planning_locked:
            return Response({'error': 'Planning is locked. Cannot complete.'},
                            status=status.HTTP_400_BAD_REQUEST)
        project.is_planning_completed = True
        project.status = 'pending_approval'
        project.save()
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @transaction.atomic
    @action(detail=True, methods=['post'], url_path='addons')
    def save_addons(self, request, pk=None):
        project = self.get_object()
        addons_list = request.data.get('addons', [])
        package_id = request.data.get('package_id')
        if package_id:
            try:
                package_obj = ProjectPackage.objects.get(type=package_id)
                project.package = package_obj
            except ProjectPackage.DoesNotExist:
                return Response({'error': f"Invalid package_id: {package_id}"},
                                status=status.HTTP_400_BAD_REQUEST)
        # Delete any previous add-on associations
        ProjectAddon.objects.filter(project=project).delete()
        package_type = project.package.type
        for addon_pk in addons_list:
            try:
                addon_obj = Addon.objects.get(pk=addon_pk, is_active=True)
                # For enterprise packages, certain add-ons might be included by default.
                included = package_type == 'enterprise' and addon_obj.compatible_packages.filter(type='enterprise').exists()
                ProjectAddon.objects.create(project=project, addon=addon_obj, is_included=included)
            except Addon.DoesNotExist:
                continue
        project.recalc_and_save()
        return Response({'detail': 'Add-ons updated successfully!', 'project_id': project.id},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        project = self.get_object()
        try:
            submission = project.planner_submission
        except PlannerSubmission.DoesNotExist:
            # Return basic project data with a warning if no submission is found.
            return Response({
                "warning": "Planner submission not yet available. Please try again later.",
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "price_eur": project.total_price_eur,
                    "features": project.package.features,
                }
            }, status=status.HTTP_200_OK)

        summary_data = {
            "project": {
                "id": project.id,
                "title": project.title,
                "price_eur": project.total_price_eur,
                "features": project.package.features,
            },
            "addons": [
                {
                    "id": pa.addon.id,
                    "title": pa.addon.name,
                    "price_eur": pa.addon.price_eur,
                } for pa in project.projectaddon_set.all()
            ],
            "planner": {
                "client_summary": submission.client_summary,
                "website_template": submission.website_template,
                "developer_notes": submission.developer_worksheet,
            },
        }
        return Response(summary_data)

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def confirm_summary(self, request, pk=None):
        project = self.get_object()
        try:
            submission = project.planner_submission
        except PlannerSubmission.DoesNotExist:
            return Response({"error": "No planner submission found."}, status=status.HTTP_400_BAD_REQUEST)
        if not submission.client_summary or not submission.developer_worksheet:
            return Response({"error": "Summary data is incomplete."}, status=status.HTTP_400_BAD_REQUEST)
        project.status = 'pending_payment'
        project.save()
        return Response({"detail": "Project summary confirmed and status updated to pending_payment."},
                        status=status.HTTP_200_OK)
