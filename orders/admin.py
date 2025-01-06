"""
Admin configuration module for ProjectOrder, OrderPayment, and CommissionPayout models.

This module handles the Django admin interface customization for project orders,
payments, and commission payouts—including display configuration, filtering
options, and summary/statistics methods.
"""

from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone

from .models import ProjectOrder, OrderPayment, CommissionPayout


@admin.register(ProjectOrder)
class ProjectOrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProjectOrder model.

    Customizes the admin interface display and functionality for project orders.

    Attributes:
        list_display: Fields shown in the list view.
        readonly_fields: Fields that cannot be modified.
        list_filter: Fields available for filtering.
        search_fields: Fields available for search functionality.
    """

    list_display = (
        "id",
        "user",
        "project_type",
        "status",
        "payment_status",
        "total_amount",
        "commission_status",
    )
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("status", "payment_status", "commission_status")
    search_fields = ("project_type", "user__email")

    def get_queryset(self, request):
        """
        Override get_queryset to optimize queries with select_related.
        """
        qs = super().get_queryset(request)
        return qs.select_related("user", "package")

    def get_commission_summary(self, request):
        """
        Example utility method for retrieving summarized commission info
        among orders with 'commission_status=pending'.
        """
        pending_qs = self.get_queryset(request).filter(commission_status='pending')

        # Sum of the commission_amount for pending orders
        total_commission = pending_qs.aggregate(
            total=Sum('commission_amount')
        )['total'] or 0

        return {
            'pending_commission': total_commission,
            'pending_count': pending_qs.count()
        }


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrderPayment model.

    Customizes the admin interface display and functionality for order payments.

    Attributes:
        list_display: Fields shown in the list view.
        list_filter: Fields available for filtering.
        search_fields: Fields available for search functionality.
    """

    list_display = ['id', 'order', 'amount', 'payment_type', 'status', 'created_at']
    list_filter = ['payment_type', 'status']
    search_fields = ['order__project_type', 'stripe_payment_id']

    def get_payment_stats(self, request):
        """
        Example utility method to get stats about today's total completed
        payments and the number of failed payments.
        """
        qs = self.get_queryset(request)
        today = timezone.now().date()

        return {
            'today_total': qs.filter(
                status='completed',
                created_at__date=today
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'failed_count': qs.filter(status='failed').count()
        }


@admin.register(CommissionPayout)
class CommissionPayoutAdmin(admin.ModelAdmin):
    """
    Admin configuration for CommissionPayout model.

    Manages viewing of payout records and their status.
    """

    list_display = ("order", "amount", "status", "payout_date")
    list_filter = ("status",)
    search_fields = ("order__id", "order__project_type")
