from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentMethodViewSet,
    PaymentPlanViewSet,
    StripeWebhookView,
    KlarnaWebhookView
)

router = DefaultRouter()
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'payment-plans', PaymentPlanViewSet, basename='payment-plan')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('webhook/klarna/', KlarnaWebhookView.as_view(), name='klarna-webhook'),
]
