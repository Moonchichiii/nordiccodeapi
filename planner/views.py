# planner/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import PlannerSubmission
from .services import AIPlanner, update_developer_worksheet

class PlannerSubmissionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id=None):
        if not project_id:
            project_id = request.data.get('project_id')
        
        if not project_id:
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = get_object_or_404(Project, id=project_id, user=request.user)
            
            # Extract submission data and project context
            submission_data = request.data.get('submission_data')
            project_context = request.data.get('project_context')

            if not submission_data or not project_context:
                return Response({"error": "Missing required data."}, status=status.HTTP_400_BAD_REQUEST)

            # Process with AI Planner
            planner = AIPlanner()
            ai_response = await planner.generate_website_plan(
                submission_data=submission_data,
                project_data={
                    'package_type': project_context['selectedPackage']['type'],
                    'package_name': project_context['selectedPackage']['name'],
                    'price_eur': project_context['selectedPackage']['price_eur'],
                    'features': project_context['selectedPackage']['features'],
                    'addons': project_context['selectedAddons'],
                    'total_price': project_context['totalPrice']
                }
            )

            # Create or update submission
            submission, created = PlannerSubmission.objects.update_or_create(
                project=project,
                defaults={
                    'submission_data': submission_data,
                    'client_summary': ai_response.get('client_summary'),
                    'website_template': ai_response.get('website_template'),
                    'developer_worksheet': ai_response.get('developer_notes')
                }
            )

            response_data = {
                'planner': {
                    'client_summary': ai_response.get('client_summary'),
                    'website_template': ai_response.get('website_template'),
                    'developer_notes': ai_response.get('developer_notes'),
                },
                'project': {
                    'id': project.id,
                    'title': project.title,
                    'package': {
                        'type': project_context['selectedPackage']['type'],
                        'name': project_context['selectedPackage']['name'],
                        'price_eur': project_context['selectedPackage']['price_eur'],
                        'features': project_context['selectedPackage']['features'],
                    },
                    'addons': project_context['selectedAddons'],
                    'total_price_eur': project_context['totalPrice']
                }
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, project_id=None):
        if not project_id:
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = get_object_or_404(Project, id=project_id)
            submission = get_object_or_404(PlannerSubmission, project=project)

            response_data = {
                'planner': {
                    'client_summary': submission.client_summary,
                    'website_template': submission.website_template,
                    'developer_notes': submission.developer_worksheet
                },
                'project': {
                    'id': project.id,
                    'title': project.title,
                    'package': {
                        'type': project.package.type,
                        'name': project.package.name,
                        'price_eur': project.package.price_eur,
                        'features': project.package.features
                    },
                    'addons': [
                        {
                            'id': pa.addon.id,
                            'title': pa.addon.name,
                            'price_eur': pa.addon.price_eur
                        } for pa in project.projectaddon_set.all()
                    ],
                    'total_price_eur': project.total_price_eur
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        except PlannerSubmission.DoesNotExist:
            return Response({"error": "No planner submission found."}, status=status.HTTP_404_NOT_FOUND)