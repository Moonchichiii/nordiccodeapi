from rest_framework import serializers

from .models import ProjectOrder


class ProjectOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOrder
        fields = "__all__"
        read_only_fields = ["id", "status", "created_at", "updated_at"]
