"""Admin configuration for CustomUser model."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin panel configuration for CustomUser model."""
    
    list_display = [
        "email", "full_name", "is_verified", "is_active", "is_staff"
    ]
    list_filter = ["is_verified", "is_active", "is_staff"]
    search_fields = ["email", "full_name"]
    ordering = ["email"]

    fieldsets = (
        (None, {
            "fields": ("email", "password")
        }),
        ("Personal Info", {
            "fields": (
                "full_name", "phone_number", "street_address", "city",
                "state_or_region", "postal_code", "country", "vat_number"
            )
        }),
        ("Status", {
            "fields": (
                "is_verified", "is_active", "accepted_terms", 
                "marketing_consent"
            )
        }),
        ("Permissions", {
            "fields": (
                "is_staff", "is_superuser", "groups", "user_permissions"
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "full_name", "phone_number", "password1", 
                "password2", "is_staff", "is_active"
            ),
        }),
    )