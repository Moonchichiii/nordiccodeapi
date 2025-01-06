"""Serializer module for ProjectOrder model.

This module provides serialization functionality for handling project order data
through the REST API.
"""
from rest_framework import serializers

from .models import ProjectOrder


class ProjectOrderSerializer(serializers.ModelSerializer):
    """Serializer for ProjectOrder model.

    Handles the conversion of ProjectOrder instances to/from JSON format.
    Includes field validation and read-only specifications.
    """

    class Meta:
        """Meta class to configure the ProjectOrderSerializer."""
        model = ProjectOrder
        fields = "__all__"
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at"
        ]
