from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone


class ProjectOrder(models.Model):
    """
    Represents an order placed by a user for a specific project package or service.
    """

    ORDER_STATUS_CHOICES = [
        ("inquiry", "Initial Inquiry"),
        ("proposal", "Proposal Sent"),
        ("deposit_pending", "Deposit Pending"),
        ("deposit_paid", "Deposit Paid"),
        ("in_progress", "In Progress"),
        ("review", "In Review"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("awaiting_deposit", "Awaiting Deposit"),
        ("deposit_paid", "Deposit Paid"),
        ("partially_paid", "Partially Paid"),
        ("completed", "Fully Paid"),
    ]

    # Commission status choices:
    COMMISSION_STATUS_CHOICES = [
        ("pending", "Commission Pending"),
        ("paid", "Commission Paid"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The user who placed this order."
    )
    package = models.ForeignKey(
        "projects.ProjectPackage",
        on_delete=models.PROTECT,
        help_text="The selected project package or tier."
    )
    project_type = models.CharField(
        max_length=100,
        help_text="Short label describing the project (e.g., 'E-commerce site')."
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the project requirements."
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="inquiry",
        help_text="General order status."
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="awaiting_deposit",
        help_text="Payment collection status."
    )

    # Financial tracking fields
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total cost of the project or package."
    )
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Upfront deposit portion."
    )
    remaining_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Outstanding amount after the deposit."
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="Commission percentage (default 20%)."
    )
    commission_status = models.CharField(
        max_length=20,
        choices=COMMISSION_STATUS_CHOICES,
        default="pending",
        help_text="Whether commission is pending or paid."
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calculated commission payout."
    )
    commission_paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp for when commission was paid."
    )

    # Additional data
    requirements = models.JSONField(
        default=list,
        help_text="JSON list of requirements or specs."
    )
    timeline = models.JSONField(
        default=dict,
        help_text="JSON structure representing milestones/deadlines."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        For a new order, automatically set deposit_amount and remaining_amount
        to 30% deposit and the rest as remaining.
        """
        if not self.pk:
            deposit = self.total_amount * Decimal("0.30")
            self.deposit_amount = deposit
            self.remaining_amount = self.total_amount - deposit
        super().save(*args, **kwargs)

    def calculate_commission(self):
        """
        Calculate commission based on total_amount and commission_rate.
        """
        return self.total_amount * (self.commission_rate / Decimal("100"))

    def process_commission(self):
        """
        Finalize commission payout if order is in 'deposit_paid' status
        and the commission_status is still 'pending'.
        """
        if self.status == "deposit_paid" and self.commission_status == "pending":
            self.commission_amount = self.calculate_commission()
            self.commission_status = "paid"
            self.commission_paid_at = timezone.now()
            self.save()

    def __str__(self):
        return f"Order #{self.pk} - {self.project_type}"


class OrderPayment(models.Model):
    """
    Represents a payment made toward a specific ProjectOrder (e.g., deposit, milestone, final).
    """

    order = models.ForeignKey(
        ProjectOrder,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_id = models.CharField(max_length=100)
    payment_type = models.CharField(
        max_length=20,
        choices=[
            ("deposit", "Initial Deposit"),
            ("milestone", "Milestone Payment"),
            ("final", "Final Payment"),
        ],
        help_text="Type of payment made (deposit, milestone, final)."
    )
    status = models.CharField(
        max_length=20,
        help_text="Payment status (e.g., pending, completed, refunded)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for Order #{self.order.pk}"


class CommissionPayout(models.Model):
    """
    A record of a commission payout (if any) associated with an order.
    """

    order = models.ForeignKey(
        ProjectOrder,
        on_delete=models.CASCADE,
        help_text="Which order the commission relates to."
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        help_text="Payout status (e.g., 'completed')."
    )
    payout_date = models.DateTimeField(
        help_text="When the commission was actually paid out."
    )

    def __str__(self):
        return f"Commission of {self.amount} for Order #{self.order.pk}"
