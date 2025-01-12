from django.contrib import admin
from .models import ProjectOrder, OrderPayment


@admin.register(ProjectOrder)
class ProjectOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "package", "total_amount", "status", "payment_status"]
    list_filter = ["status", "payment_status"]


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "amount", "payment_type", "status", "created_at"]
