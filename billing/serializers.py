from rest_framework import serializers
from .models import Payment, PaymentMethod, PaymentPlan

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'type', 'is_default', 'last_four',
            'expiry_month', 'expiry_year', 'created_at'
        ]
        read_only_fields = ['last_four', 'expiry_month', 'expiry_year', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_type', 'payment_method',
            'amount', 'status', 'paid_at', 'created_at'
        ]
        read_only_fields = ['status', 'paid_at', 'created_at']

class PaymentPlanSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    class Meta:
        model = PaymentPlan
        fields = [
            'id', 'total_amount', 'starter_fee',
            'mid_payment', 'final_payment',
            'payments', 'created_at'
        ]
        read_only_fields = ['starter_fee', 'mid_payment', 'final_payment', 'created_at']
