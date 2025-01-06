from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import stripe
from .models import OrderPayment
from .services import PaymentService, NotificationService

@require_POST
@csrf_exempt  # Required for Stripe webhooks
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object
            payment = OrderPayment.objects.get(
                stripe_payment_id=payment_intent.id
            )
            PaymentService.handle_successful_payment(payment)
            
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=400)