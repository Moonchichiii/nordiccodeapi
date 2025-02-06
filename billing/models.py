from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class PaymentPlan(models.Model):
    """Payment plan for project billing."""
    project = models.OneToOneField(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='payment_plan'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    starter_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    mid_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    final_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.starter_fee = self.total_amount * Decimal('0.25')
            self.mid_payment = self.total_amount * Decimal('0.50')
            self.final_payment = self.total_amount * Decimal('0.25')
        super().save(*args, **kwargs)

class Payment(models.Model):
    """Individual payments for a project."""
    PAYMENT_TYPES = [
        ('starter', 'Starter Fee'),
        ('milestone', 'Milestone Payment'),
        ('final', 'Final Payment')
    ]
    PAYMENT_METHODS = [
        ('card', 'Credit Card'),
        ('klarna', 'Klarna')
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]
    payment_plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent = models.CharField(max_length=100, blank=True)
    klarna_order_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PaymentMethod(models.Model):
    """Stored payment methods for users."""
    TYPES = [
        ('card', 'Credit Card'),
        ('klarna', 'Klarna')
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    type = models.CharField(max_length=20, choices=TYPES)
    is_default = models.BooleanField(default=False)
    stripe_payment_method = models.CharField(max_length=100, blank=True)
    last_four = models.CharField(max_length=4, blank=True)
    expiry_month = models.CharField(max_length=2, blank=True)
    expiry_year = models.CharField(max_length=4, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_default=True),
                name='unique_default_payment_method'
            )
        ]
