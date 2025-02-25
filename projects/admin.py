# projects/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from unfold.admin import ModelAdmin
from .models import Project, ProjectPackage, Addon, ProjectAddon

class BaseModelAdmin(ModelAdmin):
    list_per_page = 25
    save_on_top = True

@admin.register(Addon)
class AddonAdmin(BaseModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

class ProjectAddonInline(admin.TabularInline):
    model = ProjectAddon
    extra = 1
    autocomplete_fields = ['addon']

@admin.register(Project)
class ProjectAdmin(BaseModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('status',)
    autocomplete_fields = ['user', 'package']
    inlines = [ProjectAddonInline]

@admin.register(ProjectPackage)
class ProjectPackageAdmin(BaseModelAdmin):
    list_display = ('name', 'type', 'is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
