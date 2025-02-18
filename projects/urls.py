from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectPackageViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r'packages', ProjectPackageViewSet, basename='project-package')
router.register(r'', ProjectViewSet, basename='project')

app_name = 'projects'

urlpatterns = [
    path('', include(router.urls)),
]
