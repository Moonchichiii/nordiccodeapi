from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Contact

# Register your models here.


class CustomAdminSite(AdminSite):
    def get_log_entries(self, *args, **kwargs):
        return super().get_log_entries(*args, **kwargs).filter(action_flag__gte=2)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email")
    readonly_fields = ("created_at",)
