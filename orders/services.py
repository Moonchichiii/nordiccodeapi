from decimal import Decimal
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import stripe
from .models import OrderPayment, ProjectOrder

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    @staticmethod
    def calculate_milestone_payment(project, milestone):
        remaining_milestones = project.milestone_set.filter(
            is_completed=False
        ).count()
        return project.order.remaining_amount / (remaining_milestones + 1)

    @staticmethod
    def process_refund(payment, reason):
        try:
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_id,
                reason=reason
            )
            payment.status = 'refunded'
            payment.save()
            
            NotificationService.send_refund_notification(payment)
            return refund
        except stripe.error.StripeError as e:
            raise ValueError(f"Refund failed: {str(e)}")

    @staticmethod
    def handle_failed_payment_retry(payment):
        retry_count = payment.retries.count()
        if retry_count < 3:
            new_payment_intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),
                currency='usd',
                customer=payment.order.user.stripe_customer_id,
                metadata={
                    'order_id': payment.order.id,
                    'payment_type': payment.payment_type,
                    'retry_count': retry_count + 1
                }
            )
            payment.stripe_payment_id = new_payment_intent.id
            payment.save()
            return new_payment_intent
        else:
            payment.status = 'failed_permanent'
            payment.save()
            NotificationService.send_payment_failed_notification(payment)
            return None

class CommissionService:
    @staticmethod
    def calculate_commission(order):
        """Calculate commission based on order type and amount"""
        base_commission = order.total_amount * (order.commission_rate / 100)
        
        # Apply tier-based adjustments
        if order.package.name == 'enterprise':
            return base_commission * Decimal('1.2')  # 20% bonus for enterprise
        elif order.package.name == 'mid_tier':
            return base_commission * Decimal('1.1')  # 10% bonus for mid-tier
        return base_commission

    @staticmethod
    def process_commission_payout(order):
        """Process commission payout and update tracking"""
        if order.commission_status != 'pending':
            return False
            
        commission = order.commission_amount or CommissionService.calculate_commission(order)
        
        # Record commission payout
        CommissionPayout.objects.create(
            order=order,
            amount=commission,
            status='completed',
            payout_date=timezone.now()
        )
        
        order.commission_status = 'paid'
        order.commission_paid_at = timezone.now()
        order.save()
        
        return True

class NotificationService:
    @staticmethod
    def send_payment_notification(payment, template_name):
        """Send payment-related email notifications"""
        context = {
            'order_id': payment.order.id,
            'amount': payment.amount,
            'payment_type': payment.get_payment_type_display(),
            'status': payment.status,
            'project_title': payment.order.project_type
        }
        
        subject = f"Payment {payment.status.title()} - {payment.get_payment_type_display()}"
        message = render_to_string(f'orders/emails/{template_name}.txt', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.order.user.email]
        )

    @staticmethod
    def send_milestone_notification(milestone):
        """Send milestone completion notification"""
        context = {
            'milestone_title': milestone.title,
            'project_title': milestone.project.title,
            'completion_date': milestone.completion_date
        }
        
        subject = f"Milestone Completed: {milestone.title}"
        message = render_to_string('orders/emails/milestone_completed.txt', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[milestone.project.order.user.email]
        )