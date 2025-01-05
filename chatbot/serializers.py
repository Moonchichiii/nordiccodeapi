import os

import openai
from django.conf import settings
from rest_framework import serializers


class ChatbotRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1024)
    message = serializers.CharField(max_length=1024)


class ChatbotResponseSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1024)
    response = serializers.CharField(max_length=2048, read_only=True)


class ChatbotService:
    """
    Service to interact with OpenAI API.
    """

    @staticmethod
    def get_openai_response(prompt):
        """
        Get response from OpenAI API based on the given prompt.
        """
        openai.api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        try:
            response = openai.Completion.create(
                engine="davinci", prompt=prompt, max_tokens=150
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return str(e)

    @staticmethod
    def create(validated_data):
        """
        Create a response based on the validated data.
        """
        prompt = validated_data.get("prompt")
        response = ChatbotService.get_openai_response(prompt)
        return {"prompt": prompt, "response": response}
