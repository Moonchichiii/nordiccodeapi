from rest_framework import serializers
from .models import ProjectOrder, OrderPayment


class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPayment
        fields = ['id', 'amount', 'payment_type', 'status', 'created_at']
        read_only_fields = ['stripe_payment_id']


class ProjectOrderSerializer(serializers.ModelSerializer):
    payments = OrderPaymentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(
        source='get_payment_status_display',
        read_only=True
    )

    class Meta:
        model = ProjectOrder
        fields = [
            'id', 'user', 'package', 'project_type', 'description',
            'status', 'status_display', 'payment_status', 'payment_status_display',
            'total_amount', 'deposit_amount', 'remaining_amount',
            'commission_rate', 'requirements', 'timeline', 'payments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'payment_status', 'deposit_amount',
            'remaining_amount', 'created_at', 'updated_at'
        ]