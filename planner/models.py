
from django.conf import settings
from django.db import models

from projects.models import Project


class ProjectPlan(models.Model):
    """Stores AI-generated project planning data"""
    project = models.OneToOneField(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='ai_plan'
    )
    requirements_analysis = models.JSONField(default=dict)
    tech_recommendations = models.JSONField(default=dict)
    design_preferences = models.JSONField(default=dict)
    timeline_estimation = models.JSONField(default=dict)
    ai_suggestions = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def mark_complete(self):
        """Mark planning phase as complete"""
        self.project.planning_completed = True
        self.project.save()

class PlanningSession(models.Model):
    """Individual AI planning sessions"""
    plan = models.ForeignKey(
        ProjectPlan,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_type = models.CharField(max_length=50)  # requirements, design, technical
    user_input = models.JSONField()
    ai_response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
