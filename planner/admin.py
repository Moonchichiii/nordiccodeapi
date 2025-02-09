from django.contrib import admin
from .models import PlannerSubmission

@admin.register(PlannerSubmission)
class PlannerSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'has_summary', 'has_worksheet')
    list_filter = ('created_at',)
    search_fields = ('client_summary', 'developer_worksheet')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Submission Details', {
            'fields': ('submission_data', 'created_at'),
            'description': 'Raw submission data and timing'
        }),
        ('Generated Content', {
            'fields': ('client_summary', 'developer_worksheet'),
            'description': 'Generated summaries and worksheets'
        }),
    )

    def has_summary(self, obj):
        return bool(obj.client_summary)
    has_summary.boolean = True
    has_summary.short_description = "Has Summary"

    def has_worksheet(self, obj):
        return bool(obj.developer_worksheet)
    has_worksheet.boolean = True
    has_worksheet.short_description = "Has Worksheet"