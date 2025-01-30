from rest_framework import serializers

from projects.models import Project

from .models import PlanningSession, ProjectPlan


class PlanningSessionSerializer(serializers.ModelSerializer):
    """Serializer for individual planning sessions"""
    
    class Meta:
        model = PlanningSession
        fields = [
            'id',
            'session_type',
            'user_input',
            'ai_response',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def validate_session_type(self, value):
        valid_types = ['requirements', 'design', 'technical']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid session type. Must be one of: {', '.join(valid_types)}"
            )
        return value


class ProjectPlanSerializer(serializers.ModelSerializer):
    """Serializer for project plans with nested sessions"""
    
    sessions = PlanningSessionSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    
    class Meta:
        model = ProjectPlan
        fields = [
            'id',
            'project',
            'project_title',
            'requirements_analysis',
            'tech_recommendations',
            'design_preferences',
            'timeline_estimation',
            'ai_suggestions',
            'sessions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_project(self, value):
        """Ensure project is in planning phase and unlocked"""
        if value.planning_locked:
            raise serializers.ValidationError(
                "Project planning is locked. Please complete payment to proceed."
            )
        if value.planning_completed:
            raise serializers.ValidationError(
                "Project planning phase is already completed."
            )
        return value
