from rest_framework import serializers
from .models import PlannerSubmission

class PlannerSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannerSubmission
        fields = [
            'id', 
            'submission_data', 
            'client_summary', 
            'developer_worksheet', 
            'created_at'
        ]
        # Read-only: outputs are generated after submission.
        read_only_fields = ['id', 'client_summary', 'developer_worksheet', 'created_at']
