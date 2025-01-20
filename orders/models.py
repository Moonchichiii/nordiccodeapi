from decimal import Decimal

from django.conf import settings
from django.db import models


class ProjectOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ("inquiry", "Inquiry"),
        ("proposal", "Proposal Sent"),
        ("deposit_pending", "Deposit Pending"),
        ("deposit_paid", "Deposit Paid"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    package = models.ForeignKey(
        "projects.ProjectPackage",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="inquiry"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # On creation, calculate deposit/remaining amounts
            self.deposit_amount = self.total_amount * Decimal("0.30")
            self.remaining_amount = self.total_amount - self.deposit_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.pk} - {self.package}"


class OrderPayment(models.Model):
    """
    Represents a payment made for an order.
    """

    PAYMENT_TYPES = [
        ("deposit", "Deposit"),
        ("final", "Final Payment"),
    ]

    order = models.ForeignKey(
        ProjectOrder, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_id = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} for Order #{self.order.pk}"
