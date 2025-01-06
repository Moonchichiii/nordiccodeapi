"""Models for handling project orders in the Nordic Code API."""

from django.conf import settings
from django.db import models


class ProjectOrder(models.Model):
    """
    Model representing a project order in the system.

    Attributes:
        user (ForeignKey): Link to the user who created the order
        project_type (str): Type of the project ordered
        description (str): Detailed description of the project
        status (str): Current status of the order
        package (ForeignKey): Link to the project package selected
        custom_requirements (str): Additional custom requirements for the project
        timeline (dict): JSON field containing timeline information
        milestones (list): JSON field containing project milestones
        payment_status (str): Current status of payment
        created_at (datetime): Timestamp of order creation
        updated_at (datetime): Timestamp of last order update
    """

    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('completed', 'Fully Paid')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="User who created the order"
    )
    project_type = models.CharField(
        max_length=100,
        help_text="Type of project being ordered"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the project"
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="pending",
        help_text="Current status of the order"
    )
    package = models.ForeignKey(
        'projects.ProjectPackage',
        on_delete=models.PROTECT,
        help_text="Selected project package"
    )
    custom_requirements = models.TextField(
        blank=True,
        help_text="Additional custom requirements for the project"
    )
    timeline = models.JSONField(
        default=dict,
        help_text="Timeline information for the project"
    )
    milestones = models.JSONField(
        default=list,
        help_text="Project milestones"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text="Current status of payment"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the order was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the order was last updated"
    )

    def __str__(self) -> str:
        """Return a string representation of the order."""
        return f"Order #{self.pk} - {self.project_type}"
