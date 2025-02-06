# planner/views_developer.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser  # or use a custom permission
from projects.models import Project
from planner.models import PlannerSubmission
from rest_framework import status

class DeveloperWorksheetView(APIView):
    permission_classes = [IsAdminUser]  # Only admins or developers should access

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            submission = project.planner_submission
        except PlannerSubmission.DoesNotExist:
            return Response({"error": "No planner submission found for this project."},
                            status=status.HTTP_404_NOT_FOUND)

        return Response({"developerWorksheet": submission.developer_worksheet},
                        status=status.HTTP_200_OK)
