from django.urls import path

from .views import chatbot

app_name = "chatbot"

urlpatterns = [
    path("chat/", chatbot, name="chatbot"),
]
