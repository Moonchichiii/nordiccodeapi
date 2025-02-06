# planner/urls_developer.py
from django.urls import path
from .views_developer import DeveloperWorksheetView

urlpatterns = [
    path('developer/worksheet/<int:project_id>/', DeveloperWorksheetView.as_view(), name='developer-worksheet'),
]
