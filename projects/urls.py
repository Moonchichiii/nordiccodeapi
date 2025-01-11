from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, ProjectPackageViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"packages", ProjectPackageViewSet, basename="package")

urlpatterns = [
    path("", include(router.urls)),
]
