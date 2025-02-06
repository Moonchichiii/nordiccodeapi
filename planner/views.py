from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PlannerSubmission
from .serializers import PlannerSubmissionSerializer
from .services import generate_summaries
from projects.serializers import ProjectDetailSerializer
from projects.models import Project

class PlannerSubmissionAPIView(APIView):
    def post(self, request):
        project_id = request.data.get('project_id')
        try:
            project = Project.objects.get(
                id=project_id,
                user=request.user,
                status='planning'
            )
        except Project.DoesNotExist:
            return Response({"error": "Invalid project"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlannerSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save()
            try:
                summaries = generate_summaries(submission.submission_data)
                # Update project record (e.g., update title, description, etc.)
                project.title = summaries.get("project_title", "New Project")
                project.description = summaries.get("client_summary")
                # Optionally update other fields like estimated_hours if provided
                project.save()
               
                submission.client_summary = summaries.get("client_summary")
                submission.developer_worksheet = summaries.get("developer_worksheet")
                submission.save()

                return Response({
                    "submission": PlannerSubmissionSerializer(submission).data,
                    "project": ProjectDetailSerializer(project).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
