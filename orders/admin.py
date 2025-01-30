"""Admin configuration for orders app."""

from django.contrib import admin

from .models import OrderPayment, ProjectOrder


@admin.register(ProjectOrder)
class ProjectOrderAdmin(admin.ModelAdmin):
    """Admin view for ProjectOrder model."""
    
    list_display = [
        "id", "user", "package", "total_amount", "status", "payment_status"
    ]
    list_filter = ["status", "payment_status"]


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    """Admin view for OrderPayment model."""
    
    list_display = [
        "id", "order", "amount", "payment_type", "status", "created_at"
    ]
