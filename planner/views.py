import asyncio
import logging
import traceback
import json
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
from planner.services import AIPlanner, update_developer_worksheet, AIResponseError

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class PlannerSubmissionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id=None, **kwargs):
        logger.debug("Entered POST method.")
        logger.debug("Raw request.data: %s", request.data)
        logger.info("=== START Planner Submission ===")
        try:
            if not project_id:
                project_id = request.data.get('project_id')
                logger.debug("Project ID retrieved from request data: %s", project_id)
            if not project_id:
                logger.error("No project ID provided")
                return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                project = Project.objects.get(id=project_id, user=request.user, status='planning')
                logger.debug("Project found: %s", project)
            except Project.DoesNotExist:
                logger.error("Project not found: %s", project_id)
                return Response({"error": "Invalid project."}, status=status.HTTP_400_BAD_REQUEST)

            data = request.data.copy()
            submission_data = data.get('submission_data', {})
            project_context = data.get('project_context', {})
            logger.debug("Submission data: %s", submission_data)
            logger.debug("Project context: %s", project_context)

            if not submission_data:
                logger.error("No submission data provided")
                return Response({"error": "Submission data is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create the PlannerSubmission instance
            try:
                submission_instance = project.planner_submission
                logger.debug("Existing submission found: %s", submission_instance)
            except PlannerSubmission.DoesNotExist:
                submission_instance = None
                logger.debug("No existing submission found; will create new.")

            # Validate and save the submission using the serializer.
            serializer = PlannerSubmissionSerializer(
                instance=submission_instance,
                data={'submission_data': submission_data},
                context={'project': project}
            )
            serializer.is_valid(raise_exception=True)
            submission = serializer.save()
            logger.debug("Submission saved: %s", submission)

            # Normalize project_context pricing key.
            prepared_project_data = None
            if project_context:
                selected_pkg = project_context.get('selectedPackage', {})
                # Look for snake_case key first; if missing, try camelCase.
                price_eur = selected_pkg.get('price_eur')
                if price_eur is None:
                    price_eur = selected_pkg.get('priceEUR', 0)
                prepared_project_data = {
                    'package_type': selected_pkg.get('type'),
                    'package_name': selected_pkg.get('name'),
                    'price_eur': price_eur,
                    'features': selected_pkg.get('features', []),
                    'addons': project_context.get('selectedAddons', []),
                    'total_price': project_context.get('totalPrice', 0)
                }
                logger.debug("Prepared project data after key normalization: %s", prepared_project_data)
            else:
                logger.debug("No project context provided.")

            # Generate the AI plan with a timeout.
            async def generate_plan_with_timeout():
                logger.debug("Starting AIPlanner plan generation.")
                planner = AIPlanner()
                try:
                    response = await asyncio.wait_for(
                        planner.generate_website_plan(submission.submission_data, prepared_project_data),
                        timeout=60.0
                    )
                    logger.debug("AI response received successfully.")
                    return response
                except asyncio.TimeoutError:
                    logger.error("AI generation timed out")
                    raise AIResponseError("AI generation timed out")
            ai_response = async_to_sync(generate_plan_with_timeout)()
            logger.debug("AI response: %s", ai_response)

            response_data = {
                "planner": {
                    "client_summary": ai_response.get("client_summary", ""),
                    "website_template": ai_response.get("website_template", {}),
                    "developer_notes": ai_response.get("developer_notes", {})
                },
                "project": {
                    'id': project.id,
                    'title': project.title,
                    'package': {
                        'type': project.package.type,
                        'name': project.package.name,
                        'price_eur': project.package.price_eur,
                        'features': project.package.features
                    },
                    'addons': [
                        {'id': pa.addon.id, 'title': pa.addon.name, 'price_eur': pa.addon.price_eur}
                        for pa in project.projectaddon_set.all()
                    ],
                    'total_price_eur': project.total_price_eur
                }
            }
            logger.debug("Response data prepared: %s", response_data)

            try:
                website_template = ai_response.get("website_template", {})
                project.website_template = json.dumps(website_template)
                submission.website_template = json.dumps(website_template)
                project.title = ai_response.get("client_summary", "New Project")
                project.description = ai_response.get("client_summary", "")
                project.client_summary = ai_response.get("client_summary", "")
                project.generation_status = 'completed'
                project.last_planner_update = timezone.now()
                project.save()
                logger.debug("Project updated successfully: %s", project)
                submission.client_summary = ai_response.get("client_summary", "")
                submission.developer_worksheet = json.dumps(ai_response.get("developer_notes", {}))
                submission.save()
                logger.debug("Submission updated successfully: %s", submission)
                async_to_sync(update_developer_worksheet)(submission)
                logger.debug("Developer worksheet update triggered.")
            except Exception as update_error:
                logger.error("Error updating project/submission: %s", update_error)
                logger.error(traceback.format_exc())

            logger.info("Planner submission completed successfully")
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as unexpected_error:
            logger.critical("Unexpected error in planner submission: %s", unexpected_error)
            logger.critical(traceback.format_exc())
            return Response({"error": "Unexpected server error", "details": str(unexpected_error)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, project_id=None, **kwargs):
        logger.debug("Entered PATCH method.")
        if not project_id:
            project_id = request.data.get('project_id')
            logger.debug("Project ID retrieved from request data: %s", project_id)
        if not project_id:
            logger.error("No project ID provided in PATCH")
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            project = Project.objects.get(id=project_id, user=request.user, status='planning')
            logger.debug("Project found: %s", project)
        except Project.DoesNotExist:
            logger.error("Project not found in PATCH: %s", project_id)
            return Response({"error": "Invalid project."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            submission = project.planner_submission
            logger.debug("Found submission for update: %s", submission)
        except PlannerSubmission.DoesNotExist:
            logger.error("No existing submission to update for project: %s", project_id)
            return Response({"error": "No existing submission to update."}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data.pop('project_id', None)
        serializer = PlannerSubmissionSerializer(instance=submission, data=data, partial=True, context={'project': project})
        if not serializer.is_valid():
            logger.debug("Serializer errors on PATCH: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        updated_submission = serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request, project_id=None, **kwargs):
        logger.debug("Entered GET method.")
        if not project_id:
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            project = Project.objects.get(id=project_id)
            submission = project.planner_submission
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "No planner submission found for this project."}, status=status.HTTP_404_NOT_FOUND)
        
        website_template_obj = {}
        if submission.website_template:
            try:
                website_template_obj = json.loads(submission.website_template)
            except json.JSONDecodeError:
                logger.error("Error decoding website_template")
        data = {
            "client_summary": submission.client_summary,
            "website_template": website_template_obj
        }
        if request.user.is_staff:
            data["developer_worksheet"] = submission.developer_worksheet
        return Response(data, status=status.HTTP_200_OK)
