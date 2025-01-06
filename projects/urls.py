from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, PackageViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'packages', PackageViewSet, basename='package')

urlpatterns = [
    path('', include(router.urls)),
]