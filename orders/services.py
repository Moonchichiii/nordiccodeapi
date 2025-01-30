from decimal import Decimal

import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import OrderPayment, ProjectOrder

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    """Service for handling payments."""

    @staticmethod
    def calculate_milestone_payment(project: ProjectOrder, milestone) -> Decimal:
        """Calculate payment for a project milestone."""
        remaining_milestones = project.milestone_set.filter(
            is_completed=False
        ).count()
        return project.order.remaining_amount / (remaining_milestones + 1)

    @staticmethod
    def process_refund(payment: OrderPayment, reason: str):
        """Process a refund for a payment."""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_id, reason=reason
            )
            payment.status = "refunded"
            payment.save()

            NotificationService.send_refund_notification(payment)
            return refund
        except stripe.error.StripeError as e:
            raise ValueError(f"Refund failed: {str(e)}")

    @staticmethod
    def handle_failed_payment_retry(payment: OrderPayment):
        """Handle retry for a failed payment."""
        retry_count = payment.retries.count()
        if retry_count < 3:
            new_payment_intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),
                currency="usd",
                customer=payment.order.user.stripe_customer_id,
                metadata={
                    "order_id": payment.order.id,
                    "payment_type": payment.payment_type,
                    "retry_count": retry_count + 1,
                },
            )
            payment.stripe_payment_id = new_payment_intent.id
            payment.save()
            return new_payment_intent
        else:
            payment.status = "failed_permanent"
            payment.save()
            NotificationService.send_payment_failed_notification(payment)
            return None


class CommissionService:
    """Service for handling commissions."""

    @staticmethod
    def calculate_commission(order: ProjectOrder) -> Decimal:
        """Calculate commission for an order."""
        base_commission = order.total_amount * (
            order.commission_rate / Decimal("100")
        )
        if order.package.name == "enterprise":
            return base_commission * Decimal("1.2")  # 20% bonus
        elif order.package.name == "mid_tier":
            return base_commission * Decimal("1.1")  # 10% bonus
        return base_commission

    @staticmethod
    def process_commission_payout(order: ProjectOrder) -> bool:
        """Process commission payout and update tracking."""
        if order.commission_status != "pending":
            return False

        commission = order.commission_amount or CommissionService.calculate_commission(
            order
        )

        # Record commission payout
        CommissionPayout.objects.create(
            order=order,
            amount=commission,
            status="completed",
            payout_date=timezone.now(),
        )

        order.commission_status = "paid"
        order.commission_paid_at = timezone.now()
        order.save()

        return True


class NotificationService:
    """Service for sending notifications."""

    @staticmethod
    def send_payment_notification(payment: OrderPayment, notification_type: str):
        """Send payment notification."""
        subject = f"Payment {payment.status} - {payment.get_payment_type_display()}"
        message = (
            f"Payment of {payment.amount} for order {payment.order.id} "
            f"has been {payment.status}"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.order.user.email],
        )

    @staticmethod
    def send_milestone_notification(milestone):
        """Send milestone completion notification."""
        context = {
            "milestone_title": milestone.title,
            "project_title": milestone.project.title,
            "completion_date": milestone.completion_date,
        }

        subject = f"Milestone Completed: {milestone.title}"
        message = render_to_string("orders/emails/milestone_completed.txt", context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[milestone.project.order.user.email],
        )
