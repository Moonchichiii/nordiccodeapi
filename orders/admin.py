"""Admin configuration module for ProjectOrder model.

This module handles the Django admin interface customization for project orders,
including display configuration and filtering options.

Attributes:
    ProjectOrderAdmin: ModelAdmin class for ProjectOrder management.
"""

from django.contrib import admin

from .models import ProjectOrder


@admin.register(ProjectOrder)
class ProjectOrderAdmin(admin.ModelAdmin):
    """Admin configuration for ProjectOrder model.

    Customizes the admin interface display and functionality for project orders.

    Attributes:
        list_display: Fields shown in the list view.
        readonly_fields: Fields that cannot be modified.
        list_filter: Fields available for filtering.
        search_fields: Fields available for search functionality.
    """

    list_display = (
        "id",
        "user",
        "project_type",
        "status",
        "created_at",
    )
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("status", "project_type", "user")
    search_fields = ("project_type", "user__username")
