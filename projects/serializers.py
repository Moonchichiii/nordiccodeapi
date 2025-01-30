import json
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Project, ProjectPackage

User = get_user_model()
logger = logging.getLogger(__name__)


class ProjectPackageSerializer(serializers.ModelSerializer):
    """Serializer for project packages with custom validation."""

    features = serializers.JSONField(required=True)
    tech_stack = serializers.ListField(
        child=serializers.CharField(), required=True
    )
    deliverables = serializers.ListField(
        child=serializers.CharField(), required=True
    )

    class Meta:
        model = ProjectPackage
        fields = [
            "id",
            "name",
            "base_price",
            "features",
            "tech_stack",
            "deliverables",
            "estimated_duration",
            "maintenance_period",
            "sla_response_time",
        ]
        read_only_fields = ["id"]

    def validate_features(self, value: str) -> dict:
        """Validate features JSON data."""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in features: {str(e)}")
                raise serializers.ValidationError(
                    _("Invalid JSON format for features")
                )
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                _("Features must be a dictionary")
            )
        return value

    def validate_tech_stack(self, value: str) -> list:
        """Validate tech stack data."""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in tech_stack: {str(e)}")
                raise serializers.ValidationError(
                    _("Invalid JSON format for tech stack")
                )
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Tech stack must be a list")
            )
        return value

    def validate_base_price(self, value: float) -> float:
        """Validate base price."""
        if value <= 0:
            raise serializers.ValidationError(
                _("Base price must be greater than zero")
            )
        return value

    def validate(self, data: dict) -> dict:
        """Validate the entire package data."""
        if data["maintenance_period"] < 1:
            raise serializers.ValidationError(
                {"maintenance_period": _("Maintenance period cannot be negative")}
            )
        if data["sla_response_time"] < 1:
            raise serializers.ValidationError(
                {"sla_response_time": _("SLA response time must be at least 1 hour")}
            )
        return data


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for projects with enhanced validation."""

    package_name = serializers.CharField(
        source="package.get_name_display", read_only=True
    )
    user = serializers.StringRelatedField(read_only=True)
    assigned_staff = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(is_staff=True),
        required=False,
    )
    client_specifications = serializers.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
        required=False,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "user",
            "title",
            "description",
            "package",
            "package_name",
            "client_specifications",
            "status",
            "assigned_staff",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate_title(self, value: str) -> str:
        """Validate project title."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                _("Title must be at least 3 characters long")
            )
        return value.strip()

    def validate_description(self, value: str) -> str:
        """Validate project description."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                _("Description must be at least 10 characters long")
            )
        return value.strip()

    def validate_status(self, value: str) -> str:
        """Validate project status."""
        try:
            if value not in dict(Project.StatusChoices.choices):
                raise serializers.ValidationError(
                    _("Invalid status choice. Allowed values are: {}").format(
                        ", ".join(dict(Project.StatusChoices.choices).keys())
                    )
                )
        except Exception as e:
            logger.error(f"Status validation error: {str(e)}")
            raise serializers.ValidationError(_("Invalid status value"))
        return value

    def validate_package(self, value: ProjectPackage) -> ProjectPackage:
        """Validate project package."""
        if self.context["request"].method == "POST" and not value:
            raise serializers.ValidationError(_("Package is required for new projects"))
        return value

    def validate_assigned_staff(self, value: list) -> list:
        """Validate assigned staff members."""
        if value and not all(user.is_staff for user in value):
            raise serializers.ValidationError(
                _("Only staff members can be assigned to projects")
            )
        return value

    def validate(self, data: dict) -> dict:
        """Validate the entire project data."""
        try:
            if self.instance and "status" in data:
                if (
                    self.instance.status == Project.StatusChoices.COMPLETED
                    and data["status"] != Project.StatusChoices.COMPLETED
                ):
                    raise serializers.ValidationError(
                        {"status": _("Cannot change status of completed project")}
                    )
            if (
                "package" in data
                and "assigned_staff" in data
                and not data["assigned_staff"]
            ):
                logger.warning("Project created without assigned staff")
            return data
        except Exception as e:
            logger.error(f"Project validation error: {str(e)}")
            raise serializers.ValidationError(_("Invalid project data"))

    def to_representation(self, instance: Project) -> dict:
        """Custom representation of project data."""
        data = super().to_representation(instance)
        if isinstance(instance, Project):
            data["is_completed"] = instance.status == Project.StatusChoices.COMPLETED
        else:
            data["is_completed"] = (
                instance.get("status") == Project.StatusChoices.COMPLETED
            )
        return data
