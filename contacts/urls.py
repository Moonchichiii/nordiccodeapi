from django.urls import path, include
from rest_framework.routers import DefaultRouter
from contacts.views import ProjectConversationViewSet

router = DefaultRouter()
router.register("project-messages", ProjectConversationViewSet, basename="project-messages")

urlpatterns = [
    path("", include(router.urls)),
]
