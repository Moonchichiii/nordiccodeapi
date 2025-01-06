from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as django_filters

from .models import Project, ProjectPackage, Milestone, ProjectRequirement, ProjectDeliverable
from .serializers import (
    ProjectSerializer,
    ProjectCreateUpdateSerializer,
    ProjectPackageSerializer,
    MilestoneSerializer,
    ProjectRequirementSerializer,
    ProjectDeliverableSerializer
)


class ProjectFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(lookup_expr="iexact")
    featured = django_filters.BooleanFilter()
    year = django_filters.CharFilter()
    services = django_filters.CharFilter(lookup_expr="icontains")
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Project
        fields = ["category", "featured", "year", "services"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(services__icontains=value) |
            Q(location__icontains=value)
        )


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProjectFilter
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectSerializer

    @action(detail=True, methods=['post'])
    def add_requirement(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectRequirementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_milestone(self, request, pk=None):
        project = self.get_object()
        serializer = MilestoneSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete_milestone(self, request, pk=None):
        project = self.get_object()
        milestone = get_object_or_404(
            Milestone,
            project=project,
            id=request.data.get('milestone_id')
        )
        milestone.is_completed = True
        milestone.completion_date = timezone.now().date()
        milestone.save()
        return Response(MilestoneSerializer(milestone).data)

    @action(detail=True, methods=['post'])
    def upload_deliverable(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectDeliverableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProjectPackage.objects.all()
    serializer_class = ProjectPackageSerializer

    @action(detail=True, methods=['get'])
    def features(self, request, pk=None):
        package = self.get_object()
        return Response({
            'features': package.features,
            'tech_stack': package.tech_stack,
            'deliverables': package.deliverables,
            'details': {
                'name': package.get_name_display(),
                'base_price': package.base_price,
                'estimated_duration': package.estimated_duration,
                'maintenance_period': package.maintenance_period,
                'sla_response_time': package.sla_response_time
            }
        })

    @action(detail=True, methods=['post'])
    def calculate_estimate(self, request, pk=None):
        package = self.get_object()
        requirements = request.data.get('requirements', [])
        complexity = request.data.get('complexity', 'medium')

        complexity_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.3
        }

        total_price = float(package.base_price)
        total_price *= complexity_multipliers.get(complexity, 1.0)

        estimated_duration = package.estimated_duration
        if len(requirements) > 5:
            estimated_duration += (len(requirements) * 2)

        return Response({
            'base_price': package.base_price,
            'estimated_total': total_price,
            'estimated_duration': estimated_duration,
            'complexity_factor': complexity_multipliers.get(complexity, 1.0),
            'requirements_count': len(requirements)
        })
