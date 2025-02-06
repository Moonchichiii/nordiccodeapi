from django.urls import include, path
from .admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/users/", include("users.urls")),
    path("api/chat/", include("chat.urls")),
    path('api/projects/', include('projects.urls')),
    path("api/billing/", include("billing.urls")),
    path("api/planner/", include("planner.urls")),
    path("api/planner/", include("planner.urls_developer")),
    path("api/chatbot/", include("chatbot.urls")),
]