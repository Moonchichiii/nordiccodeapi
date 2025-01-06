from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectOrderViewSet,
    CommissionDashboardView,
    PaymentReportView
)

router = DefaultRouter()
router.register(r'orders', ProjectOrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns += [
    path('admin/commission-dashboard/', 
         CommissionDashboardView.as_view(), 
         name='commission-dashboard'),
    path('admin/payment-reports/', 
         PaymentReportView.as_view(), 
         name='payment-reports'),
]