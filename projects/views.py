from django_filters import rest_framework as filters
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import (
    Project,
    ProjectPackage,
    Milestone,
    ProjectRequirement,
    ProjectDeliverable
)
from .serializers import (
    ProjectSerializer,
    ProjectDetailSerializer,
    ProjectCreateUpdateSerializer,
    ProjectPackageSerializer,
    MilestoneSerializer,
    ProjectRequirementSerializer,
    ProjectDeliverableSerializer
)

class ProjectFilter(filters.FilterSet):
    """Filter set for Project model."""
    
    category = filters.CharFilter(field_name="category", lookup_expr="iexact")
    featured = filters.BooleanFilter(field_name="featured")
    year = filters.CharFilter(field_name="year")
    services = filters.CharFilter(field_name="services", lookup_expr="icontains")
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Project
        fields = ["category", "featured", "year", "services"]
    
    def filter_search(self, queryset, name, value):
        """Custom search filter across multiple fields."""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(services__icontains=value) |
            Q(location__icontains=value)
        )

class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for handling all project operations."""
    
    queryset = Project.objects.all()
    filterset_class = ProjectFilter
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Select appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectSerializer

    @action(detail=True, methods=['post'])
    def add_requirement(self, request, pk=None):
        """Add a new requirement to the project."""
        project = self.get_object()
        serializer = ProjectRequirementSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_milestone(self, request, pk=None):
        """Add a new milestone to the project."""
        project = self.get_object()
        serializer = MilestoneSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upload_deliverable(self, request, pk=None):
        """Upload a new deliverable for the project."""
        project = self.get_object()
        serializer = ProjectDeliverableSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get project timeline with milestones and deliverables."""
        project = self.get_object()
        milestones = project.milestone_set.all().order_by('due_date')
        deliverables = project.projectdeliverable_set.all().order_by('uploaded_at')
        
        return Response({
            'milestones': MilestoneSerializer(milestones, many=True).data,
            'deliverables': ProjectDeliverableSerializer(deliverables, many=True).data,
            'requirements': ProjectRequirementSerializer(
                project.projectrequirement_set.all(), many=True
            ).data
        })

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update project status and handle related actions."""
        project = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Project.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project.status = new_status
        project.save()
        
        return Response({'status': new_status})

class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for project packages with custom actions."""
    
    queryset = ProjectPackage.objects.all()
    serializer_class = ProjectPackageSerializer
    
    @action(detail=True, methods=['get'])
    def features(self, request, pk=None):
        """Get detailed features for a package."""
        package = self.get_object()
        return Response({
            'features': package.features,
            'details': {
                'name': package.get_name_display(),
                'base_price': package.base_price,
                'estimated_duration': package.estimated_duration
            }
        })

    @action(detail=True, methods=['post'])
    def calculate_estimate(self, request, pk=None):
        """Calculate custom estimate based on requirements."""
        package = self.get_object()
        requirements = request.data.get('requirements', [])
        
        # Base price from package
        total_price = float(package.base_price)
        
        # Add complexity factor
        complexity = request.data.get('complexity', 'medium')
        complexity_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.3
        }
        total_price *= complexity_multipliers.get(complexity, 1.0)
        
        # Adjust duration based on requirements
        estimated_duration = package.estimated_duration
        if len(requirements) > 5:
            estimated_duration += len(requirements) * 2
        
        return Response({
            'base_price': package.base_price,
            'estimated_total': total_price,
            'estimated_duration': estimated_duration,
            'complexity_factor': complexity_multipliers.get(complexity, 1.0),
            'requirements_count': len(requirements)
        })

class ProjectProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for tracking project progress."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        """Filter projects by authenticated user."""
        return Project.objects.filter(order__user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get detailed progress information for a project."""
        project = self.get_object()
        milestones = project.milestone_set.all()
        completed = milestones.filter(is_completed=True)
        
        next_milestone = milestones.filter(is_completed=False).first()
        next_milestone_data = MilestoneSerializer(next_milestone).data if next_milestone else None
        
        # Calculate overall progress including requirements
        requirements = project.projectrequirement_set.all()
        requirements_progress = (
            requirements.filter(is_completed=True).count() / requirements.count() * 100
            if requirements.exists() else 0
        )
        
        milestone_progress = (
            completed.count() / milestones.count() * 100
            if milestones.exists() else 0
        )
        
        # Weight milestones more heavily in overall progress
        overall_progress = (milestone_progress * 0.7 + requirements_progress * 0.3)
        
        return Response({
            'overall_progress': round(overall_progress, 1),
            'milestone_progress': round(milestone_progress, 1),
            'requirements_progress': round(requirements_progress, 1),
            'completed_milestones': completed.count(),
            'total_milestones': milestones.count(),
            'next_milestone': next_milestone_data,
            'recent_deliverables': ProjectDeliverableSerializer(
                project.projectdeliverable_set.order_by('-uploaded_at')[:5],
                many=True
            ).data,
            'upcoming_milestones': MilestoneSerializer(
                milestones.filter(is_completed=False).order_by('due_date')[:3],
                many=True
            ).data
        })

    @action(detail=True, methods=['post'])
    def complete_milestone(self, request, pk=None):
        """Mark a milestone as completed."""
        project = self.get_object()
        milestone_id = request.data.get('milestone_id')
        milestone = get_object_or_404(Milestone, project=project, id=milestone_id)
        
        milestone.is_completed = True
        milestone.completion_date = timezone.now().date()
        milestone.save()
        
        return Response(MilestoneSerializer(milestone).data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get project summary including all related data."""
        project = self.get_object()
        
        return Response({
            'project': ProjectDetailSerializer(project).data,
            'progress': self.progress(request, pk).data,
            'timeline': ProjectViewSet.timeline(self, request, pk).data
        })


