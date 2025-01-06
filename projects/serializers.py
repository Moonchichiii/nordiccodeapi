"""Project serializer module for the Nordic Code API.

This module provides serialization for Project model instances using Django REST Framework.
"""
from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model.

    This serializer handles the conversion of Project model instances to JSON format
    and vice versa, including all relevant fields for project representation.
    """

    class Meta:
        """Meta class to configure the ProjectSerializer."""
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "location",
            "services",
            "year",
            "image",
            "category",
            "link",
            "external_link",
            "featured",
        ]


from rest_framework import serializers
from .models import (
    Project,
    ProjectPackage,
    ProjectRequirement,
    Milestone,
    ProjectDeliverable
)

class ProjectDeliverableSerializer(serializers.ModelSerializer):
    """Serializer for project deliverables."""
    
    class Meta:
        model = ProjectDeliverable
        fields = [
            'id',
            'title',
            'file',
            'version',
            'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']

class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for project milestones."""
    
    days_until_due = serializers.SerializerMethodField()
    
    class Meta:
        model = Milestone
        fields = [
            'id',
            'title',
            'description',
            'due_date',
            'is_completed',
            'completion_date',
            'days_until_due'
        ]
        read_only_fields = ['completion_date']
    
    def get_days_until_due(self, obj):
        """Calculate days until milestone is due."""
        if obj.due_date:
            from django.utils import timezone
            import datetime
            today = timezone.now().date()
            delta = obj.due_date - today
            return delta.days
        return None

class ProjectRequirementSerializer(serializers.ModelSerializer):
    """Serializer for project requirements."""
    
    class Meta:
        model = ProjectRequirement
        fields = [
            'id',
            'requirement_type',
            'details',
            'is_completed'
        ]

class ProjectPackageSerializer(serializers.ModelSerializer):
    """Serializer for project packages."""
    
    display_name = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectPackage
        fields = [
            'id',
            'name',
            'display_name',
            'base_price',
            'features',
            'features_list',
            'estimated_duration'
        ]
    
    def get_display_name(self, obj):
        """Get the human-readable name of the package."""
        return obj.get_name_display()
    
    def get_features_list(self, obj):
        """Convert JSON features field to a formatted list."""
        if isinstance(obj.features, list):
            return obj.features
        return []

class ProjectSerializer(serializers.ModelSerializer):
    """Main serializer for projects with nested related data."""
    
    requirements = ProjectRequirementSerializer(
        source='projectrequirement_set',
        many=True,
        read_only=True
    )
    milestones = MilestoneSerializer(
        source='milestone_set',
        many=True,
        read_only=True
    )
    deliverables = ProjectDeliverableSerializer(
        source='projectdeliverable_set',
        many=True,
        read_only=True
    )
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'location',
            'services',
            'year',
            'image',
            'category',
            'link',
            'external_link',
            'featured',
            'created_at',
            'order',
            'requirements',
            'milestones',
            'deliverables',
            'progress_percentage'
        ]
        read_only_fields = ['created_at']
    
    def get_progress_percentage(self, obj):
        """Calculate the overall progress of the project."""
        milestones = obj.milestone_set.all()
        if not milestones.exists():
            return 0
        completed = milestones.filter(is_completed=True).count()
        total = milestones.count()
        return round((completed / total) * 100, 1)

class ProjectDetailSerializer(ProjectSerializer):
    """Extended serializer for detailed project view."""
    
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + [
            'requirements_count',
            'milestones_count',
            'deliverables_count'
        ]
    
    requirements_count = serializers.SerializerMethodField()
    milestones_count = serializers.SerializerMethodField()
    deliverables_count = serializers.SerializerMethodField()
    
    def get_requirements_count(self, obj):
        return obj.projectrequirement_set.count()
    
    def get_milestones_count(self, obj):
        return obj.milestone_set.count()
    
    def get_deliverables_count(self, obj):
        return obj.projectdeliverable_set.count()

class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating projects."""
    
    requirements = ProjectRequirementSerializer(many=True, required=False)
    milestones = MilestoneSerializer(many=True, required=False)
    
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'location',
            'services',
            'year',
            'image',
            'category',
            'link',
            'external_link',
            'featured',
            'order',
            'requirements',
            'milestones'
        ]
    
    def create(self, validated_data):
        """Handle nested creation of requirements and milestones."""
        requirements_data = validated_data.pop('requirements', [])
        milestones_data = validated_data.pop('milestones', [])
        
        project = Project.objects.create(**validated_data)
        
        for requirement_data in requirements_data:
            ProjectRequirement.objects.create(project=project, **requirement_data)
        
        for milestone_data in milestones_data:
            Milestone.objects.create(project=project, **milestone_data)
        
        return project
    
    def update(self, instance, validated_data):
        """Handle nested updates of requirements and milestones."""
        requirements_data = validated_data.pop('requirements', [])
        milestones_data = validated_data.pop('milestones', [])
        
        # Update project instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create requirements
        if requirements_data:
            instance.projectrequirement_set.all().delete()
            for requirement_data in requirements_data:
                ProjectRequirement.objects.create(
                    project=instance,
                    **requirement_data
                )
        
        # Update or create milestones
        if milestones_data:
            instance.milestone_set.all().delete()
            for milestone_data in milestones_data:
                Milestone.objects.create(
                    project=instance,
                    **milestone_data
                )
        
        return instance