from django.urls import path
from .views import PlannerSubmissionAPIView

urlpatterns = [
    path('submissions/', PlannerSubmissionAPIView.as_view(), name='planner-submissions'),
    path('submissions/<int:project_id>/', PlannerSubmissionAPIView.as_view(), name='planner-submission-detail'),
]
