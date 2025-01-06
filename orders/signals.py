from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import ProjectOrder, OrderPayment

@receiver(post_save, sender=ProjectOrder)
def order_status_changed(sender, instance, created, **kwargs):
    if not created and hasattr(instance, 'tracker') and instance.tracker.has_changed('status'):
        send_status_notification(instance)

@receiver(post_save, sender=OrderPayment)
def payment_status_changed(sender, instance, created, **kwargs):
    if not created and hasattr(instance, 'tracker') and instance.tracker.has_changed('status'):
        if instance.status == 'completed':
            handle_completed_payment(instance)

def handle_completed_payment(payment):
    order = payment.order
    if payment.payment_type == 'deposit':
        order.status = 'deposit_paid'
        order.payment_status = 'deposit_paid'
        order.save()
        # Create associated project
        from projects.models import Project
        Project.objects.create(
            order=order,
            title=f"Project for {order.project_type}",
            description=order.description,
            status='planning'
        )

def get_notification_template(order_status):
    templates = {
        'inquiry': 'emails/orders/inquiry_received.txt',
        'proposal': 'emails/orders/proposal_sent.txt',
        'deposit_paid': 'emails/orders/deposit_confirmed.txt',
        'in_progress': 'emails/orders/project_started.txt',
        'completed': 'emails/orders/project_completed.txt'
    }
    return templates.get(order_status, 'emails/orders/status_update.txt')