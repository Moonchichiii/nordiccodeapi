import asyncio
import json
import logging
import traceback
from asgiref.sync import async_to_sync, sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from projects.models import Project
from planner.models import PlannerSubmission
from planner.serializers import PlannerSubmissionSerializer
from planner.services import (
    AIPlanner, 
    EnhancedAIPlanner,
    ProjectContext,
    update_developer_worksheet, 
    AIResponseError
)

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class PlannerSubmissionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id=None, **kwargs):
        logger.info("=== START Planner Submission ===")
        try:
            # Validate project ID
            if not project_id:
                project_id = request.data.get('project_id')
            if not project_id:
                logger.error("No project ID provided")
                return Response(
                    {"error": "Project ID is required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Retrieve project
            try:
                project = Project.objects.get(
                    id=project_id,
                    user=request.user,
                    status='planning'
                )
            except Project.DoesNotExist:
                logger.error(f"Project not found: {project_id}")
                return Response(
                    {"error": "Invalid project."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract submission data and project context from request
            data = request.data.copy()
            submission_data = data.get('submission_data', {})
            project_context = data.get('project_context', {})

            if not submission_data:
                logger.error("No submission data provided")
                return Response(
                    {"error": "Submission data is required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create or update the PlannerSubmission
            serializer = PlannerSubmissionSerializer(
                instance=project.planner_submission if hasattr(project, 'planner_submission') else None,
                data={'submission_data': submission_data},
                partial=True,
                context={'project': project}
            )
            try:
                serializer.is_valid(raise_exception=True)
                submission = serializer.save()
            except Exception as serializer_error:
                logger.error(f"Serializer validation error: {serializer_error}")
                return Response(
                    {"error": "Invalid submission data", "details": str(serializer_error)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create a cleaned project context without pricing information
            cleaned_context = ProjectContext(
                package_type=project_context.get('selectedPackage', {}).get('type'),
                package_name=project_context.get('selectedPackage', {}).get('name'),
                features=project_context.get('selectedPackage', {}).get('features', []),
                selected_addons=[
                    addon.get('title') for addon in project_context.get('selectedAddons', [])
                ],
                business_goals=submission_data.get('businessGoals', {}).get('primaryPurpose', [])
            )

            # Generate AI response with timeout handling
            try:
                async def generate_plan_with_timeout():
                    planner = EnhancedAIPlanner()
                    try:
                        return await asyncio.wait_for(
                            planner.generate_complete_plan(
                                submission.submission_data,
                                cleaned_context
                            ),
                            timeout=120.0  # 120 seconds timeout
                        )
                    except asyncio.TimeoutError:
                        logger.error("AI generation timed out")
                        raise AIResponseError("AI generation timed out")

                ai_response = async_to_sync(generate_plan_with_timeout)()

            except AIResponseError as ai_error:
                logger.error(f"AI Response Error: {ai_error}")
                return Response(
                    {"error": "Failed to generate AI response", "details": str(ai_error)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as gen_error:
                logger.error(f"Unexpected error in AI generation: {gen_error}")
                logger.error(traceback.format_exc())
                return Response(
                    {"error": "Unexpected error in AI generation", "details": str(gen_error)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Update project and submission with AI-generated content
            try:
                project.title = ai_response.get("client_summary", "New Project")[:200]
                project.description = ai_response.get("client_summary", "")
                project.client_summary = ai_response.get("client_summary", "")
                project.website_template = ai_response.get("website_template", "")
                project.generation_status = 'completed'
                project.last_planner_update = timezone.now()
                project.save()

                submission.client_summary = ai_response.get("client_summary", "")
                submission.website_template = ai_response.get("website_template", "")
                submission.developer_worksheet = json.dumps(ai_response.get("developer_notes", {}))
                submission.save()

                # Schedule background task for further developer worksheet updates
                async_to_sync(update_developer_worksheet)(submission)

            except Exception as update_error:
                logger.error(f"Error updating project/submission: {update_error}")
                logger.error(traceback.format_exc())
                # Continue to return response even if update fails

            # Prepare response data (omitting any pricing information)
            response_data = {
                "planner": {
                    "client_summary": ai_response.get("client_summary", ""),
                    "website_template": ai_response.get("website_template", ""),
                    "developer_notes": ai_response.get("developer_notes", {})
                },
                "project": {
                    'id': project.id,
                    'title': project.title,
                    'status': project.status,
                    'package': {
                        'type': project.package.type,
                        'name': project.package.name,
                        'features': project.package.features,
                    }
                }
            }

            logger.info("Planner submission completed successfully")
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as unexpected_error:
            logger.critical(f"Unexpected error in planner submission: {unexpected_error}")
            logger.critical(traceback.format_exc())
            return Response(
                {"error": "Unexpected server error", "details": str(unexpected_error)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, project_id=None, **kwargs):
        """Handle partial update of an existing planner submission"""
        logger.debug("=== PATCH Request Data ===")
        if not project_id:
            project_id = request.data.get('project_id')
        logger.debug(f"Using Project ID: {project_id}")

        if not project_id:
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(id=project_id, user=request.user, status='planning')
            logger.debug(f"Found project: {project}")
        except Project.DoesNotExist:
            return Response({"error": "Invalid project."}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(project, 'planner_submission'):
            return Response({"error": "No existing submission to update."}, status=status.HTTP_404_NOT_FOUND)

        submission_instance = project.planner_submission
        data = request.data.copy()
        data.pop('project_id', None)
        logger.debug(f"Processed update data: {data}")

        serializer = PlannerSubmissionSerializer(
            instance=submission_instance,
            data=data,
            partial=True,
            context={'project': project}
        )
        if not serializer.is_valid():
            logger.debug(f"Serializer errors on PATCH: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        updated_submission = serializer.save()
        logger.debug(f"Updated submission: {updated_submission}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request, project_id=None, **kwargs):
        """Retrieve planner submission details"""
        logger.debug("=== GET Request ===")
        if not project_id:
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = Project.objects.get(id=project_id)
            submission = project.planner_submission
            logger.debug(f"Found project: {project}")
            logger.debug(f"Found submission: {submission}")
        except Project.DoesNotExist:
            logger.debug("Project not found")
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.debug(f"Error finding submission: {str(e)}")
            return Response({"error": "No planner submission found for this project."}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "client_summary": submission.client_summary,
            "website_template": submission.website_template,
        }
        if request.user.is_staff:
            data["developer_worksheet"] = submission.developer_worksheet
        
        logger.debug(f"Response data: {data}")
        return Response(data, status=status.HTTP_200_OK)
