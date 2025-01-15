from django.contrib import admin
from django.urls import path, include, re_path
from allauth.account.views import confirm_email
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    re_path(
        r"^accounts/confirm-email/(?P<key>[-:\w]+)/$",
        confirm_email,
        name="account_confirm_email",
    ),
    path(
        "auth/verification-sent/",
        TemplateView.as_view(template_name="account/email_verification_sent.html"),
        name="account_email_verification_sent",
    ),
    path("api/contacts/", include("contacts.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/chatbot/", include("chatbot.urls")),
]
