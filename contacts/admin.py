"""Contact administration module for the Nordic Code API.

This module defines the admin interface configurations for Contact models.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Contact


class CustomAdminSite(AdminSite):
    """Custom admin site with filtered log entries."""

    def get_log_entries(self, *args, **kwargs):
        """Filter log entries to show only specific action flags.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            QuerySet: Filtered log entries where action_flag is >= 2.
        """
        return super().get_log_entries(*args, **kwargs).filter(action_flag__gte=2)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin configuration for Contact model."""

    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email")
    readonly_fields = ("created_at",)
