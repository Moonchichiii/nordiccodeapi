import logging
from rest_framework import serializers
from .models import PlannerSubmission

logger = logging.getLogger(__name__)

class PlannerSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerSubmission
        fields = [
            'id',
            'submission_data',
            'client_summary',
            'website_template',
            'developer_worksheet',
            'created_at'
        ]
        read_only_fields = ['id', 'client_summary', 'website_template', 'developer_worksheet', 'created_at']

    def validate(self, attrs):
        if not self.context.get('project'):
            logger.error("Project not provided in serializer context")
            raise serializers.ValidationError("Project must be provided")
        logger.debug("Serializer validate() input attrs: %s", attrs)
        return attrs

    def create(self, validated_data):
        project = self.context.get('project')
        logger.debug("Creating submission with validated data: %s", validated_data)
        if not project:
            raise serializers.ValidationError("Project must be provided")
        instance = PlannerSubmission.objects.create(
            project=project,
            submission_data=validated_data.get('submission_data')
        )
        logger.debug("Created submission instance: %s", instance)
        return instance
