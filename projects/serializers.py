from rest_framework import serializers
from .models import Project, ProjectPackage


class ProjectSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(
        source="package.get_name_display", read_only=True
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "package",
            "package_name",
            "client_specifications",
            "status",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ProjectPackageSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = ProjectPackage
        fields = [
            "id",
            "name",
            "display_name",
            "base_price",
            "features",
            "tech_stack",
            "deliverables",
            "estimated_duration",
            "maintenance_period",
            "sla_response_time",
        ]
