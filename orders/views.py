from decimal import Decimal
import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import OrderPayment, ProjectOrder
from .serializers import ProjectOrderSerializer
from .services import NotificationService, PaymentService

stripe.api_key = settings.STRIPE_SECRET_KEY


class ProjectOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "payment_status"]
    search_fields = ["id", "package__name"]
    ordering_fields = ["created_at", "total_amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            ProjectOrder.objects.select_related("user", "package")
            .prefetch_related("payments")
            .filter(user=self.request.user)
        )

    @transaction.atomic
    def perform_create(self, serializer):
        order = serializer.save(
            user=self.request.user, status="inquiry", payment_status="awaiting_deposit"
        )
        self.calculate_amounts(order)

    def calculate_amounts(self, order):
        order.deposit_amount = order.total_amount * Decimal("0.30")
        order.remaining_amount = order.total_amount - order.deposit_amount
        order.save(update_fields=["deposit_amount", "remaining_amount"])

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save()
        if "status" in serializer.validated_data:
            instance.status = serializer.validated_data["status"]
            instance.save(update_fields=["status"])

    @action(detail=True, methods=["post"])
    def process_deposit(self, request, pk=None):
        order = self.get_object()

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(order.deposit_amount * 100),
                currency="usd",
                customer=request.user.stripe_customer_id,
                metadata={"order_id": order.id, "payment_type": "deposit"},
            )

            payment = OrderPayment.objects.create(
                order=order,
                amount=order.deposit_amount,
                stripe_payment_id=payment_intent.id,
                payment_type="deposit",
                status="pending",
            )

            return Response(
                {
                    "client_secret": payment_intent.client_secret,
                    "payment_id": payment.id,
                }
            )
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirm_deposit(self, request, pk=None):
        order = self.get_object()
        payment = get_object_or_404(
            OrderPayment, order=order, payment_type="deposit", status="pending"
        )

        try:
            stripe_payment = stripe.PaymentIntent.retrieve(payment.stripe_payment_id)

            if stripe_payment.status == "succeeded":
                payment.status = "completed"
                payment.save(update_fields=["status"])

                order.payment_status = "deposit_paid"
                order.status = "deposit_paid"
                order.save(update_fields=["payment_status", "status"])

                NotificationService.send_payment_notification(
                    payment, "payment_success"
                )
                return Response({"status": "deposit_confirmed"})

            return Response(
                {"error": "Payment not succeeded"}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def process_milestone_payment(self, request, pk=None):
        order = self.get_object()
        milestone_id = request.data.get("milestone_id")

        if not milestone_id:
            return Response(
                {"error": "milestone_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = PaymentService.calculate_milestone_payment(order, milestone_id)
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency="usd",
                customer=request.user.stripe_customer_id,
                metadata={
                    "order_id": order.id,
                    "payment_type": "milestone",
                    "milestone_id": milestone_id,
                },
            )

            payment = OrderPayment.objects.create(
                order=order,
                amount=amount,
                stripe_payment_id=payment_intent.id,
                payment_type="milestone",
                status="pending",
            )

            return Response(
                {
                    "client_secret": payment_intent.client_secret,
                    "payment_id": payment.id,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommissionDashboardView(TemplateView):
    template_name = "orders/commission_dashboard.html"
    permission_classes = [IsAdminUser]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_commissions"] = ProjectOrder.objects.filter(
            commission_status="pending"
        )
        context["total_commission_pending"] = sum(
            order.calculate_commission() for order in context["pending_commissions"]
        )
        return context


class PaymentReportView(TemplateView):
    template_name = "orders/payment_report.html"
    permission_classes = [IsAdminUser]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_payments"] = OrderPayment.objects.filter(status="completed")
        context["recent_payments"] = OrderPayment.objects.filter(
            status="completed"
        ).order_by("-created_at")[:10]
        return context
