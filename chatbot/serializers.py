"""
Serializers and service for chatbot functionality using OpenAI API.

This module provides serializers for handling chatbot requests/responses and a service
class for interacting with the OpenAI API.
"""

import os
from typing import Dict, Any

import openai
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import APIException


class ChatbotRequestSerializer(serializers.Serializer):
    """Serializer for chatbot request data."""

    prompt = serializers.CharField(max_length=1024)
    message = serializers.CharField(max_length=1024)

    def create(self, validated_data):
class ChatbotResponseSerializer(serializers.Serializer):
    """Serializer for chatbot response data."""

    prompt = serializers.CharField(max_length=1024)
    response = serializers.CharField(
        max_length=2048,
        read_only=True
    )

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        instance.update(validated_data)
        return instance
    """Serializer for chatbot response data."""

    prompt = serializers.CharField(max_length=1024)
    response = serializers.CharField(
        max_length=2048,
        read_only=True
    )


class OpenAIServiceError(APIException):
    """Custom exception for OpenAI service errors."""

    status_code = 503
    default_detail = 'OpenAI service error'


class ChatbotService:
    """Service class to handle interactions with OpenAI API."""

    @staticmethod
    def get_openai_response(prompt: str) -> str:
        """
        Get response from OpenAI API based on the given prompt.

        Args:
            prompt: Input text to send to OpenAI API.

        Returns:
            str: Generated response from OpenAI.

        Raises:
            OpenAIServiceError: If API call fails or returns invalid response.
        """
        openai.api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        try:
            response = openai.Completion.create(
                engine="davinci",
                prompt=prompt,
                max_tokens=150
            )
            return response.choices[0].text.strip()
        except (openai.error.OpenAIError, KeyError, IndexError) as exc:
            raise OpenAIServiceError(detail=str(exc)) from exc

    @staticmethod
    def create(validated_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create a response based on the validated data.

        Args:
            validated_data: Dictionary containing validated request data.

        Returns:
            Dict containing prompt and generated response.
        """
        prompt = validated_data.get("prompt")
        response = ChatbotService.get_openai_response(prompt)
        return {"prompt": prompt, "response": response}
