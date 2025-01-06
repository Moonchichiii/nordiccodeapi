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
