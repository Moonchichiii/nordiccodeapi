# In users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["email", "is_staff", "is_active", "is_verified"]
    list_filter = ["is_staff", "is_active", "is_verified"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_verified")}),
        ("Personal Info", {"fields": ("full_name", "phone_number")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "is_verified",
                ),
            },
        ),
    )
    search_fields = ["email"]
    ordering = ["email"]


admin.site.register(CustomUser, CustomUserAdmin)
