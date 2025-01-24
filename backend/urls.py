"""URL configuration for the backend application."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/users/", include("users.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/projects/", include("projects.urls")),
     path("api/planner/", include("planner.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/chatbot/", include("chatbot.urls")),
]
