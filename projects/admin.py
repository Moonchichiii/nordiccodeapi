"""
Admin configuration for Project model in the Nordic Code API.

This module defines the admin interface customization for Project models,
including display configurations, form customizations, and media assets.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Configure the admin interface for Project model.

    Attributes:
        list_display: Fields to display in the list view.
        list_editable: Fields that can be edited from the list view.
        search_fields: Fields available for searching.
        list_filter: Fields available for filtering.
        readonly_fields: Fields that cannot be edited.
        ordering: Default ordering of records.
    """

    list_display = (
        "title",
        "location",
        "services",
        "year",
        "featured",
        "display_tags",
        "order",
    )
    list_editable = ("order", "featured")
    search_fields = ("title", "description", "location", "services")
    list_filter = ("featured", "year", "services")
    readonly_fields = ("created_at",)
    ordering = ("order", "-created_at")

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "description", "location", "services", "year")},
        ),
        ("Media & Links", {"fields": ("image", "link", "external_link")}),
        ("Organization", {"fields": ("tags", "featured", "order")}),
        ("System Fields", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def display_tags(self, obj):
        """Format project tags as a comma-separated string.

        Args:
            obj: Project instance being displayed.

        Returns:
            str: Comma-separated list of tags or '-' if no tags exist.
        """
        if not getattr(obj, "tags", None):
            return "-"
        try:
            tags_list = (
                obj.tags if isinstance(obj.tags, list) else eval(obj.tags)
            )
            return ", ".join(tags_list)
        except (ValueError, SyntaxError):
            return "-"

    display_tags.short_description = "Tags"

    def get_form(self, request, obj=None, **kwargs):
        """Customize form field help texts.

        Args:
            request: The current HTTP request.
            obj: The object being edited, or None for new objects.
            **kwargs: Additional keyword arguments.

        Returns:
            ModelForm: Customized form with updated help texts.
        """
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["order"].help_text = "Lower numbers appear first"
        form.base_fields["tags"].help_text = (
            'Enter tags as a Python list, e.g., ["Design", "Development"]'
        )
        form.base_fields["link"].help_text = (
            "Internal path, e.g., /portfolio/project-name"
        )
        return form

    class Media:
        """Define custom CSS and JavaScript files for the admin interface."""

        css = {"all": ("admin/css/project_admin.css",)}
        js = ("admin/js/project_admin.js",)


from django.contrib import admin
from .models import Project, ProjectPackage, ProjectRequirement, Milestone, ProjectDeliverable

@admin.register(ProjectPackage)
class ProjectPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'estimated_duration')
    list_filter = ('name',)

@admin.register(ProjectRequirement)
class ProjectRequirementAdmin(admin.ModelAdmin):
    list_display = ('project', 'requirement_type', 'is_completed')
    list_filter = ('is_completed', 'requirement_type')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'due_date', 'is_completed')
    list_filter = ('is_completed',)

@admin.register(ProjectDeliverable)
class ProjectDeliverableAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'version', 'uploaded_at')