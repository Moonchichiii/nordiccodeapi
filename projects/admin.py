# projects/admin.py
from django.contrib import admin
from .models import Project, ProjectPackage, Addon, ProjectAddon

class ProjectAddonInline(admin.TabularInline):
    model = ProjectAddon
    extra = 1
    readonly_fields = ("added_at",)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "user_email", "package_name", "status", "is_planning_locked", "total_price_eur", "created_at")
    list_filter = ("status", "package__type", "is_planning_locked")
    search_fields = ("title", "description", "user__email")
    date_hierarchy = "created_at"
    inlines = [ProjectAddonInline]
    fieldsets = (
        (None, {
            "fields": ("user", "title", "description", "status", "requirements_doc",
                       ("start_date", "target_completion_date"), "is_planning_completed", "is_planning_locked", "total_price_eur")
        }),
        ("Package", {"fields": ("package",)}),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"

    def package_name(self, obj):
        return obj.package.name
    package_name.short_description = "Package"

@admin.register(ProjectPackage)
class ProjectPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "price_eur", "price_sek", "is_active", "is_recommended", "created_at")
    list_filter = ("type", "is_active", "is_recommended")
    search_fields = ("name", "description")
    date_hierarchy = "created_at"

@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ("name", "price_eur", "price_sek", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    date_hierarchy = "created_at"
    filter_horizontal = ("compatible_packages",)

@admin.register(ProjectAddon)
class ProjectAddonAdmin(admin.ModelAdmin):
    list_display = ("project", "addon", "is_included", "added_at")
    list_filter = ("is_included", "addon__name", "project__title")
    search_fields = ("project__title", "addon__name")
    date_hierarchy = "added_at"
