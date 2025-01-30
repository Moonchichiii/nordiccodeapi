"""Admin configuration for Project and ProjectPackage models."""

from django.contrib import admin

from .models import Project, ProjectPackage


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin view for Project model."""
    
    list_display = (
        "title", "user", "package", "status", "created_at"
    )
    list_filter = ("status", "package")
    search_fields = ("title", "description")


@admin.register(ProjectPackage)
class ProjectPackageAdmin(admin.ModelAdmin):
    """Admin view for ProjectPackage model."""
    
    list_display = (
        "name", "base_price", "estimated_duration"
    )
    list_filter = ("name",)
