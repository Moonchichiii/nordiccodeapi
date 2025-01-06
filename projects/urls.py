from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectDetailView, 
    ProjectListView, 
    PackageViewSet,
    ProjectProgressViewSet
)

router = DefaultRouter()
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'progress', ProjectProgressViewSet, basename='progress')

urlpatterns = [
    path("", include(router.urls)),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
]