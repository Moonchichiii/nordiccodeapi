# billing/admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import PaymentPlan, Payment, PaymentMethod

class BaseModelAdmin(ModelAdmin):
    list_per_page = 25
    save_on_top = True

@admin.register(PaymentPlan)
class PaymentPlanAdmin(BaseModelAdmin):
    list_display = ('id', 'project', 'total_amount', 'created_at')
    search_fields = ('project__title',)

@admin.register(Payment)
class PaymentAdmin(BaseModelAdmin):
    list_display = ('id', 'payment_plan', 'amount', 'status', 'created_at')
    search_fields = ('payment_plan__project__title',)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(BaseModelAdmin):
    list_display = ('id', 'user', 'type', 'is_default', 'created_at')
    search_fields = ('user__email',)
