import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.log import getLogger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import OrderPayment
from .services import PaymentService

logger = getLogger(__name__)


@require_POST
@csrf_exempt
def stripe_webhook(request) -> HttpResponse:
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    try:
        if event["type"] == "payment_intent.succeeded":
            handle_payment_intent_succeeded(event["data"]["object"])
        else:
            logger.warning(f"Unhandled event type: {event['type']}")

        return HttpResponse(status=200)
    except Exception as e:
        logger.exception(f"Error processing webhook event: {e}")
        return JsonResponse({"error": "Webhook processing failed"}, status=500)


def handle_payment_intent_succeeded(payment_intent: dict) -> None:
    """Handle the 'payment_intent.succeeded' event from Stripe."""
    try:
        payment = OrderPayment.objects.get(stripe_payment_id=payment_intent["id"])
        payment.status = "completed"
        payment.save()

        payment.order.payment_status = (
            "partially_paid" if payment.payment_type == "milestone" else "completed"
        )
        payment.order.save()

        logger.info(
            f"Payment {payment_intent['id']} marked as completed. "
            f"Order {payment.order.id} updated to {payment.order.payment_status}."
        )
    except OrderPayment.DoesNotExist:
        logger.error(f"Payment with Stripe ID {payment_intent['id']} not found.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
