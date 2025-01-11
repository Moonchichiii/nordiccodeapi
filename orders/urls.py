from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ProjectOrderViewSet

router = DefaultRouter()
router.register(r"orders", ProjectOrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
]
