"""URL configuration module for the backend application.

This module defines the URL routing patterns for the entire backend application,
including admin, API endpoints, and authentication routes.

Routes:
    - /admin/: Django admin interface
    - /api/contacts/: Contact management API
    - /api/projects/: Project management API
    - /api/orders/: Order management API
    - /api/chatbot/: Chatbot interaction API
    - /auth/: Authentication endpoints
    - /auth/registration/: User registration endpoints
"""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/contacts/", include("contacts.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/chatbot/", include("chatbot.urls")),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
]
