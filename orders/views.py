import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import ProjectOrder, OrderPayment
from .serializers import ProjectOrderSerializer, OrderPaymentSerializer
from backend.permissions import IsOrderOwner

stripe.api_key = settings.STRIPE_SECRET_KEY


class ProjectOrderViewSet(viewsets.ModelViewSet):
    """
    Manages CRUD operations for ProjectOrder.
    Only authenticated users can access orders, and we filter to the orders belonging to the user.
    An additional permission class (IsOrderOwner) can be applied to enforce that only order owners can manage their orders.
    """
    serializer_class = ProjectOrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwner]

    def get_queryset(self):
        # Show only orders owned by the logged-in user
        return ProjectOrder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically associates the created order with the logged-in user.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def process_deposit(self, request, pk=None):
        """
        Creates a Stripe PaymentIntent for the deposit amount,
        and an OrderPayment record with status='pending'.
        """
        order = self.get_object()

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(order.deposit_amount * 100),  # Convert to cents
                currency='usd',
                customer=request.user.stripe_customer_id,
                metadata={'order_id': order.id, 'payment_type': 'deposit'}
            )

            OrderPayment.objects.create(
                order=order,
                amount=order.deposit_amount,
                stripe_payment_id=payment_intent.id,
                payment_type='deposit',
                status='pending'
            )

            return Response({'client_secret': payment_intent.client_secret})
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_deposit(self, request, pk=None):
        """
        Checks the Stripe PaymentIntent status and, if succeeded,
        marks the order deposit as completed (status='deposit_paid').
        """
        order = self.get_object()

        payment = get_object_or_404(
            OrderPayment,
            order=order,
            payment_type='deposit',
            status='pending'
        )

        try:
            stripe_payment = stripe.PaymentIntent.retrieve(payment.stripe_payment_id)

            if stripe_payment.status == 'succeeded':
                payment.status = 'completed'
                payment.save()

                order.payment_status = 'deposit_paid'
                order.status = 'deposit_paid'
                order.save()

                return Response({'status': 'deposit_confirmed'})

            return Response({'error': 'Payment not succeeded'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommissionDashboardView(TemplateView):
    """
    A read-only admin view for summarizing 'pending' commissions.
    """
    template_name = 'orders/commission_dashboard.html'
    permission_classes = [IsAdminUser]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_commissions'] = ProjectOrder.objects.filter(commission_status='pending')
        context['total_commission_pending'] = sum(
            order.calculate_commission() for order in context['pending_commissions']
        )
        return context


class PaymentReportView(TemplateView):
    """
    A read-only admin view for summarizing completed payments and recent payment history.
    """
    template_name = 'orders/payment_report.html'
    permission_classes = [IsAdminUser]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_payments'] = OrderPayment.objects.filter(status='completed')
        context['recent_payments'] = OrderPayment.objects.filter(
            status='completed'
        ).order_by('-created_at')[:10]
        return context
