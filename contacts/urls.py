from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MarkConversationReadView,
    ProjectConversationViewSet,
    ProjectMessageViewSet,
)

router = DefaultRouter()
router.register(r"conversations", ProjectConversationViewSet, basename="conversations")
router.register(r"messages", ProjectMessageViewSet, basename="messages")

app_name = "contacts"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "conversations/<int:pk>/mark-read/",
        MarkConversationReadView.as_view(),
        name="conversations-mark-read",
    ),
]
