from django.contrib import admin
from ..builder.models import PlannerSubmission

@admin.register(PlannerSubmission)
class PlannerSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    readonly_fields = ('client_summary', 'developer_worksheet', 'created_at')
