from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectOrderViewSet

router = DefaultRouter()
router.register(r"", ProjectOrderViewSet, basename="order")

app_name = "orders"

urlpatterns = [
    path("", include(router.urls)),
]
