from rest_framework.routers import DefaultRouter
from .views import ProjectConversationViewSet, ProjectMessageViewSet

router = DefaultRouter()
router.register("conversations", ProjectConversationViewSet, basename="conversations")
router.register("messages", ProjectMessageViewSet, basename="messages")

urlpatterns = router.urls
