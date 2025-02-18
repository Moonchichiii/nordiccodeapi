from rest_framework import serializers
from .models import PlannerSubmission

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
            raise serializers.ValidationError("Project must be provided")
        return attrs

    def create(self, validated_data):
        project = self.context.get('project')
        if not project:
            raise serializers.ValidationError("Project must be provided")
        instance = PlannerSubmission.objects.create(
            project=project,
            submission_data=validated_data.get('submission_data')
        )
        return instance
