from django.contrib import admin
from .models import PaymentPlan, Payment, PaymentMethod

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_amount', 'created_at')
    readonly_fields = ('starter_fee', 'mid_payment', 'final_payment', 'created_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment_type', 'amount', 'status', 'created_at')
    readonly_fields = ('paid_at', 'created_at')

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'is_default', 'created_at')
    readonly_fields = ('last_four', 'expiry_month', 'expiry_year', 'created_at')
