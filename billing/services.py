import stripe
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any
from .models import Payment, PaymentPlan, PaymentMethod

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    """Service for handling payments and payment methods."""
    
    @staticmethod
    async def create_payment_plan(project_id: int, total_amount: Decimal) -> PaymentPlan:
        return await PaymentPlan.objects.acreate(
            project_id=project_id,
            total_amount=total_amount
        )

    @staticmethod
    async def initiate_starter_payment(
        payment_plan_id: int,
        payment_method: str,
        return_url: str
    ) -> Dict[str, Any]:
        payment_plan = await PaymentPlan.objects.aget(id=payment_plan_id)
        payment = await Payment.objects.acreate(
            payment_plan=payment_plan,
            payment_type='starter',
            payment_method=payment_method,
            amount=payment_plan.starter_fee
        )
        if payment_method == 'card':
            return await StripeService.create_payment_intent(payment, return_url)
        else:
            return await KlarnaService.create_order(payment, return_url)

    @staticmethod
    async def store_payment_method(
        user_id: int,
        payment_method_id: str,
        set_default: bool = False
    ) -> PaymentMethod:
        stripe_method = stripe.PaymentMethod.retrieve(payment_method_id)
        if set_default:
            await PaymentMethod.objects.filter(
                user_id=user_id,
                is_default=True
            ).aupdate(is_default=False)
        return await PaymentMethod.objects.acreate(
            user_id=user_id,
            type='card',
            stripe_payment_method=payment_method_id,
            last_four=stripe_method.card.last4,
            expiry_month=stripe_method.card.exp_month,
            expiry_year=stripe_method.card.exp_year,
            is_default=set_default
        )

    @staticmethod
    async def process_payment_success(payment_intent_id: str) -> None:
        payment = await Payment.objects.aget(stripe_payment_intent=payment_intent_id)
        payment.status = 'completed'
        payment.paid_at = timezone.now()
        await payment.asave()
        if payment.payment_type == 'starter':
            project = payment.payment_plan.project
            project.status = 'planning'
            project.is_planning_locked = False
            await project.asave()

class StripeService:
    """Service for Stripe-specific operations."""
    
    @staticmethod
    async def create_payment_intent(payment: Payment, return_url: str) -> Dict[str, Any]:
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency='eur',
                payment_method_types=['card'],
                metadata={
                    'payment_id': payment.id,
                    'project_id': payment.payment_plan.project_id,
                    'payment_type': payment.payment_type
                }
            )
            payment.stripe_payment_intent = intent.id
            await payment.asave()
            return {
                'payment_url': None,  # Handled client-side (Stripe Elements)
                'client_secret': intent.client_secret,
                'payment_id': payment.id
            }
        except stripe.error.StripeError as e:
            payment.status = 'failed'
            await payment.asave()
            raise e

class KlarnaService:
    """Service for Klarna-specific operations."""
    
    @staticmethod
    async def create_order(payment: Payment, return_url: str) -> Dict[str, Any]:
        # Placeholder implementation for Klarna integration.
        return {
            'payment_url': f'https://klarna.com/placeholder/{payment.id}',
            'order_id': f'klarna_{payment.id}'
        }
