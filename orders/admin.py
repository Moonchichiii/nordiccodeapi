"""
Admin configuration for ProjectOrder model.

Customizes the admin interface display and functionality for project orders.
Fields shown in list view: ID, user, project type, status, and creation date.
Allows filtering by status, project type and user.
Enables search by project type and username.
"""

from django.contrib import admin

from .models import ProjectOrder

# Register your models here.


@admin.register(ProjectOrder)
class ProjectOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "project_type", "status", "created_at")
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("status", "project_type", "user")
    search_fields = ("project_type", "user__username")
