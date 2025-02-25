# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin, UserAdmin):
    list_display = ('email', 'full_name', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)

    # Optionally, override fieldsets if you need more customization
    fieldsets = (
        ("Account Information", {'fields': ('email', 'password', 'is_active', 'is_staff')}),
        ("Personal Information", {'fields': ('full_name', 'phone_number')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'password1', 'password2'),
        }),
    )
