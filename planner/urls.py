from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PlanningSessionViewSet, ProjectPlanViewSet

router = DefaultRouter()
router.register(r'plans', ProjectPlanViewSet, basename='plan')
router.register(r'sessions', PlanningSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]