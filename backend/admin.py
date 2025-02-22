from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib import admin
from django.contrib.admin import AdminSite

from django.urls import path, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.html import format_html
from django.db.models import Sum

from projects.models import Project
from billing.models import Payment
from users.models import CustomUser

@require_POST
def toggle_sidebar(request):
    """
    Toggle the sidebar open/closed state in the user session.
    """
    current = request.session.get('sidebar_open', True)
    request.session['sidebar_open'] = not current
    return JsonResponse({'sidebar_open': request.session['sidebar_open']})

class CustomAdminSite(AdminSite):
    site_header = 'Nordic Code Works Management'
    site_title = 'Site Management'
    index_title = 'Dashboard'
    
    def get_app_list(self, request, *args, **kwargs):
        """
        Customize the app list by filtering out unwanted apps.
        """
        app_list = super().get_app_list(request, *args, **kwargs)
        return [app for app in app_list if app['name'] != 'Auth']

    def get_urls(self):
        """
        Append custom URL patterns (e.g. for toggling the sidebar) to the default admin URLs.
        """
        urls = super().get_urls()
        custom_urls = [
            path('toggle_sidebar/', self.admin_view(toggle_sidebar), name='toggle_sidebar'),
        ]
        return custom_urls + urls

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

    @admin.display(description="Preview")
    def view_site_button(self, obj):
        """
        Return a button linking to the live site preview if the project is active.
        """
        if obj.status == 'active':
            return format_html(
                '<a class="button" href="{}" target="_blank">View Live Site</a>',
                f'/preview/{obj.id}'
            )
        return "Not Live"

    @admin.display(description="Payment Status")
    def payment_status(self, obj):
        """
        Compute the payment status based on the total paid versus total price.
        """
        total_paid = Payment.objects.filter(
            payment_plan__project=obj, 
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        percentage = (total_paid / obj.total_price_eur * 100) if obj.total_price_eur else 0
        
        if percentage >= 100:
            return format_html('<span style="color: green;">Paid</span>')
        elif percentage > 0:
            return format_html('<span style="color: orange;">{:.0f}% Paid</span>', percentage)
        return format_html('<span style="color: red;">Unpaid</span>')

    @admin.display(description="User Email")
    def user_email(self, obj):
        """
        Return the email of the associated user.
        """
        return getattr(obj.user, 'email', '-')

    @admin.display(description="Package")
    def package_display(self, obj):
        """
        Return the package name if available.
        """
        return obj.package.name if obj.package else "-"

class PaymentAdmin(ModelAdmin):
    list_display = ('id', 'project_link', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_type')
    search_fields = ('payment_plan__project__title', 'id')
    readonly_fields = ('created_at', 'paid_at')

    fieldsets = (
        ('Payment Details', {
            'fields': ('payment_plan', 'amount', 'payment_type', 'status'),
            'description': 'Basic payment information'
        }),
        ('Timing', {
            'fields': ('created_at', 'paid_at'),
            'description': 'Payment timing details'
        }),
    )

    def get_queryset(self, request):
        """
        Optimize the queryset by selecting related project via payment_plan.
        """
        qs = super().get_queryset(request)
        return qs.select_related('payment_plan__project')

    @admin.display(description="Project")
    def project_link(self, obj):
        """
        Return a clickable link to the related project's change page.
        """
        project = getattr(obj.payment_plan, 'project', None)
        if project:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:projects_project_change', args=[project.id]),
                project.title
            )
        return "N/A"

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
            'fields': ('street_address', 'city', 'state_or_region', 'postal_code', 'country'),
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

    @admin.display(description="Projects")
    def projects_count(self, obj):
        """
        Display the count of projects associated with the user as a clickable link.
        """
        count = Project.objects.filter(user=obj).count()
        url = f"{reverse('admin:projects_project_changelist')}?user__id__exact={obj.id}"
        return format_html('<a href="{}">{} projects</a>', url, count)

# Register models with the custom admin site
admin_site.register(Project, ProjectAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(CustomUser, CustomUserAdmin)
