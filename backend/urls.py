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

"""
URL configuration for the backend application.
Includes routes for admin, contact, projects, chatbot APIs, and authentication endpoints.
Authentication endpoints include:
- POST /auth/login/
- POST /auth/logout/
- POST /auth/password/reset/
- POST /auth/registration/
- POST /auth/registration/account-confirm-email/<key>/
"""
