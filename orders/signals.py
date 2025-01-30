import logging
from typing import Dict

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone

from chat.models import ProjectConversation
from projects.models import Project

from .models import OrderPayment, ProjectOrder

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProjectOrder)
def order_status_changed(sender, instance: ProjectOrder, created: bool, **kwargs):
    """Handle order status changes and trigger notifications."""
    if not created and hasattr(instance, "tracker") and instance.tracker.has_changed("status"):
        send_status_notification(instance)


@receiver(post_save, sender=OrderPayment)
def payment_status_changed(sender, instance: OrderPayment, created: bool, **kwargs):
    """Handle payment status changes and trigger appropriate actions."""
    if not created and hasattr(instance, "tracker") and instance.tracker.has_changed("status"):
        if instance.status == "completed":
            handle_completed_payment(instance)


def handle_completed_payment(payment: OrderPayment):
    """Handle completed payment and create/update associated resources."""
    order = payment.order
    if payment.payment_type == "deposit":
        order.status = "deposit_paid"
        order.payment_status = "deposit_paid"
        order.save()

        project = Project.objects.create(
            order=order,
            title=f"Project for {order.project_type}",
            description=order.description,
            status="planning",
            planning_locked=False
        )

        ProjectConversation.objects.get_or_create(
            project=project,
            defaults={'is_active': True}
        )

        send_mail(
            subject="Payment Received - Project Planning Unlocked",
            message=(
                "Your initial payment has been received. You can now access the "
                "project planner to begin designing your project."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
        )


def get_notification_template(order_status: str) -> str:
    """Return the appropriate email template for the given order status."""
    templates: Dict[str, str] = {
        "inquiry": "emails/orders/inquiry_received.txt",
        "proposal": "emails/orders/proposal_sent.txt",
        "deposit_paid": "emails/orders/deposit_confirmed.txt",
        "in_progress": "emails/orders/project_started.txt",
        "completed": "emails/orders/project_completed.txt",
    }
    return templates.get(order_status, "emails/orders/status_update.txt")


def send_status_notification(instance: ProjectOrder):
    """Send email notifications for order status changes."""
    template = get_notification_template(instance.status)
    context = {
        'order': instance,
        'status': instance.get_status_display(),
    }

    message = render_to_string(template, context)
    send_mail(
        subject=f"Order Status Update - {instance.get_status_display()}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instance.user.email],
    )
