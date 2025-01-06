from rest_framework import serializers
from .models import (Project, ProjectPackage, ProjectRequirement,
                    Milestone, ProjectDeliverable, ProjectComment)


class ProjectRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRequirement
        fields = ['id', 'requirement_type', 'details', 'is_completed']


class MilestoneSerializer(serializers.ModelSerializer):
    days_until_due = serializers.SerializerMethodField()
    
    class Meta:
        model = Milestone
        fields = ['id', 'title', 'description', 'due_date', 'is_completed',
                 'completion_date', 'days_until_due', 'order']
        read_only_fields = ['completion_date']
    
    def get_days_until_due(self, obj):
        if obj.due_date:
            from django.utils import timezone
            today = timezone.now().date()
            return (obj.due_date - today).days
        return None


class ProjectDeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDeliverable
        fields = ['id', 'title', 'file', 'version', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class ProjectCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = ProjectComment
        fields = ['id', 'message', 'created_at', 'attachments', 'user_name']
        read_only_fields = ['created_at']


class ProjectPackageSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='get_name_display', read_only=True)
    
    class Meta:
        model = ProjectPackage
        fields = ['id', 'name', 'display_name', 'base_price', 'features',
                 'tech_stack', 'deliverables', 'estimated_duration',
                 'maintenance_period', 'sla_response_time']


class ProjectSerializer(serializers.ModelSerializer):
    requirements = ProjectRequirementSerializer(source='projectrequirement_set',
                                             many=True, read_only=True)
    milestones = MilestoneSerializer(source='milestone_set',
                                   many=True, read_only=True)
    deliverables = ProjectDeliverableSerializer(source='projectdeliverable_set',
                                              many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display',
                                         read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'location', 'services',
                 'year', 'image', 'category', 'link', 'external_link',
                 'featured', 'status', 'status_display', 'created_at',
                 'order', 'requirements', 'milestones', 'deliverables']
        read_only_fields = ['created_at']


class ProjectCreateUpdateSerializer(ProjectSerializer):
    requirements = ProjectRequirementSerializer(many=True, required=False)
    milestones = MilestoneSerializer(many=True, required=False)
    
    def create(self, validated_data):
        requirements_data = validated_data.pop('requirements', [])
        milestones_data = validated_data.pop('milestones', [])
        
        project = Project.objects.create(**validated_data)
        
        for req_data in requirements_data:
            ProjectRequirement.objects.create(project=project, **req_data)
        for mile_data in milestones_data:
            Milestone.objects.create(project=project, **mile_data)
        
        return project

    def update(self, instance, validated_data):
        requirements_data = validated_data.pop('requirements', [])
        milestones_data = validated_data.pop('milestones', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if requirements_data:
            instance.projectrequirement_set.all().delete()
            for req_data in requirements_data:
                ProjectRequirement.objects.create(project=instance, **req_data)
        
        if milestones_data:
            instance.milestone_set.all().delete()
            for mile_data in milestones_data:
                Milestone.objects.create(project=instance, **mile_data)
        
        return instance