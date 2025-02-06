from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
import stripe

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
                await PaymentService.process_payment_success(
                    event.data.object.id
                )

            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=400)

@method_decorator(csrf_exempt, name='dispatch')
class KlarnaWebhookView(APIView):
    async def post(self, request, *args, **kwargs):
        # Implement Klarna webhook handling
        return HttpResponse(status=200)