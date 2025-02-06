from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import admin
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.contrib.admin import ModelAdmin 


from projects.models import Project
from billing.models import Payment
from users.models import CustomUser


class CustomAdminSite(AdminSite):
    site_header = 'Nordic Code Works Management'
    site_title = 'Site Management'
    index_title = 'Dashboard'

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        return app_list

admin_site = CustomAdminSite(name='admin')

class ProjectAdmin(ModelAdmin):
    list_display = (
        'title', 
        'user_email', 
        'status', 
        'package_display',
        'payment_status',
        'view_site_button'
    )
    list_filter = ('status', 'package__type', 'is_planning_locked')
    search_fields = ('title', 'user__email')
    readonly_fields = ('created_at', 'total_price_eur')
    
    fieldsets = (
        ('Project Overview', {
            'fields': ('title', 'description', 'status'),
            'description': 'Basic project information'
        }),
        ('Client Information', {
            'fields': ('user', 'requirements_doc'),
            'description': 'Client details and requirements'
        }),
        ('Package & Pricing', {
            'fields': ('package', 'total_price_eur'),
            'description': 'Project package and financial details'
        }),
        ('Timeline', {
            'fields': ('start_date', 'target_completion_date'),
            'description': 'Project timeline information'
        }),
    )

    def view_site_button(self, obj):
        if obj.status == 'active':
            return format_html(
                '<a class="button" href="{}" target="_blank">View Live Site</a>',
                f'/preview/{obj.id}'
            )
        return "Not Live"
    view_site_button.short_description = "Preview"

    def payment_status(self, obj):
        total_paid = Payment.objects.filter(
            project=obj, 
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        percentage = (total_paid / obj.total_price_eur * 100) if obj.total_price_eur else 0
        
        if percentage >= 100:
            return format_html('<span style="color: green;">Paid</span>')
        elif percentage > 0:
            return format_html(
                '<span style="color: orange;">{:.0f}% Paid</span>', 
                percentage
            )
        return format_html('<span style="color: red;">Unpaid</span>')
    payment_status.short_description = "Payment Status"

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"

    def package_display(self, obj):
        return obj.package.name if obj.package else "-"
    package_display.short_description = "Package"

class PaymentAdmin(ModelAdmin):
    list_display = ('id', 'project_link', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_type')
    search_fields = ('project__title', 'id')
    readonly_fields = ('created_at', 'paid_at')

    fieldsets = (
        ('Payment Details', {
            'fields': ('project', 'amount', 'payment_type', 'status'),
            'description': 'Basic payment information'
        }),
        ('Timing', {
            'fields': ('created_at', 'paid_at'),
            'description': 'Payment timing details'
        }),
    )

    def project_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:projects_project_change', args=[obj.project.id]),
            obj.project.title
        )
    project_link.short_description = "Project"

class CustomUserAdmin(ModelAdmin):
    list_display = ('email', 'full_name', 'projects_count', 'is_active')
    list_filter = ('is_active', 'is_verified')
    search_fields = ('email', 'full_name')
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'full_name', 'phone_number'),
            'description': 'Basic contact information'
        }),
        ('Address', {
            'fields': ('street_address', 'city', 'state_or_region', 
                      'postal_code', 'country'),
            'description': 'Client address details'
        }),
        ('Business Information', {
            'fields': ('vat_number',),
            'description': 'Business-related information'
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_verified', 'last_login'),
            'description': 'Account status and activity'
        }),
    )

    def projects_count(self, obj):
        count = Project.objects.filter(user=obj).count()
        return format_html(
            '<a href="{}?user__id__exact={}">{} projects</a>',
            reverse('admin:projects_project_changelist'),
            obj.id,
            count
        )
    projects_count.short_description = "Projects"

# Register models with the custom admin site
admin_site.register(Project, ProjectAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(CustomUser, CustomUserAdmin)