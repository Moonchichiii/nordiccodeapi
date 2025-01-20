from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectPackageViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"packages", ProjectPackageViewSet, basename="package")
router.register(r"", ProjectViewSet, basename="project")

app_name = "projects"

urlpatterns = [
    path("", include(router.urls)),
]
