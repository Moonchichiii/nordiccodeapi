from rest_framework import serializers

from .models import OrderPayment, ProjectOrder


class OrderPaymentSerializer(serializers.ModelSerializer):
    """Serializer for OrderPayment model."""

    class Meta:
        model = OrderPayment
        fields = ["id", "amount", "payment_type", "status", "created_at"]
        read_only_fields = ["stripe_payment_id"]


class ProjectOrderSerializer(serializers.ModelSerializer):
    """Serializer for ProjectOrder model."""
    
    payments = OrderPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectOrder
        fields = [
            "id",
            "user",
            "package",
            "total_amount",
            "deposit_amount",
            "remaining_amount",
            "status",
            "payment_status",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]
