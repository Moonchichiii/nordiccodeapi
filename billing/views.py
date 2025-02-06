from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
import stripe
from django.conf import settings
from .services import PaymentService
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PaymentMethod, PaymentPlan
from .serializers import PaymentMethodSerializer, PaymentPlanSerializer

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    async def post(self, request, *args, **kwargs):
        try:
            event = stripe.Webhook.construct_event(
                payload=request.body,
                sig_header=request.headers.get('stripe-signature'),
                secret=settings.STRIPE_WEBHOOK_SECRET
            )
            if event.type == 'payment_intent.succeeded':
                await PaymentService.process_payment_success(event.data.object.id)
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=400)

@method_decorator(csrf_exempt, name='dispatch')
class KlarnaWebhookView(APIView):
    async def post(self, request, *args, **kwargs):
        # Implement Klarna webhook handling as needed.
        return HttpResponse(status=200)

class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payment methods."""
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    async def add_card(self, request):
        try:
            payment_method = await PaymentService.store_payment_method(
                user_id=request.user.id,
                payment_method_id=request.data.get('payment_method_id'),
                set_default=request.data.get('set_default', False)
            )
            serializer = self.get_serializer(payment_method)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    async def set_default(self, request, pk=None):
        payment_method = await self.get_object()
        await PaymentMethod.objects.filter(user=request.user, is_default=True).aupdate(is_default=False)
        payment_method.is_default = True
        await payment_method.asave()
        serializer = self.get_serializer(payment_method)
        return Response(serializer.data)

class PaymentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment plans."""
    serializer_class = PaymentPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentPlan.objects.filter(project__user=self.request.user).prefetch_related('payments')

    @action(detail=True, methods=['post'])
    async def initiate_starter_payment(self, request, pk=None):
        payment_plan = await self.get_object()
        try:
            result = await PaymentService.initiate_starter_payment(
                payment_plan_id=payment_plan.id,
                payment_method=request.data.get('payment_method'),
                return_url=request.data.get('return_url')
            )
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
