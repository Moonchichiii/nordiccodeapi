from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PlanningSession, ProjectPlan
from .serializers import PlanningSessionSerializer, ProjectPlanSerializer
from .services import AIPlanner


class ProjectPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for project plans with AI integration"""
    serializer_class = ProjectPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectPlan.objects.filter(
            project__user=self.request.user
        ).select_related('project').prefetch_related('sessions')

    @action(detail=True, methods=['post'])
    async def analyze_requirements(self, request, pk=None):
        """Trigger AI analysis of project requirements"""
        plan = self.get_object()
        
        try:
            analysis = await AIPlanner.analyze_requirements(
                project_type=plan.project.package.name,
                requirements=request.data
            )
            
            plan.requirements_analysis = analysis
            plan.save()
            
            # Create session record
            PlanningSession.objects.create(
                plan=plan,
                session_type='requirements',
                user_input=request.data,
                ai_response=analysis
            )
            
            return Response(analysis)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    async def get_design_recommendations(self, request, pk=None):
        """Get AI-powered design recommendations"""
        plan = self.get_object()
        
        try:
            recommendations = await AIPlanner.get_design_recommendations(
                requirements=plan.requirements_analysis,
                preferences=request.data
            )
            
            plan.design_preferences = recommendations
            plan.save()
            
            PlanningSession.objects.create(
                plan=plan,
                session_type='design',
                user_input=request.data,
                ai_response=recommendations
            )
            
            return Response(recommendations)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    async def get_tech_recommendations(self, request, pk=None):
        """Get AI-powered tech stack recommendations"""
        plan = self.get_object()
        
        try:
            recommendations = await AIPlanner.get_tech_stack_recommendations(
                project_type=plan.project.package.name,
                requirements=plan.requirements_analysis
            )
            
            plan.tech_recommendations = recommendations
            plan.save()
            
            PlanningSession.objects.create(
                plan=plan,
                session_type='technical',
                user_input=plan.requirements_analysis,
                ai_response=recommendations
            )
            
            return Response(recommendations)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def complete_planning(self, request, pk=None):
        """Mark planning phase as complete"""
        plan = self.get_object()
        
        if not all([
            plan.requirements_analysis,
            plan.tech_recommendations,
            plan.design_preferences
        ]):
            return Response(
                {'error': 'All planning phases must be completed first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.mark_complete()
        return Response({'status': 'planning completed'})


class PlanningSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing planning session history"""
    serializer_class = PlanningSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlanningSession.objects.filter(
            plan__project__user=self.request.user
        ).select_related('plan', 'plan__project')

