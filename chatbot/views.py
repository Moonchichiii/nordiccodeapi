"""Views for the chatbot application handling message processing and responses."""

import logging
from typing import Optional, List

from django.conf import settings
from django.core.cache import cache
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from langdetect import detect_langs
from openai import APIError, OpenAI, RateLimitError, Timeout
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .hash import hash_message


# Initialize OpenAI client and logger
client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def get_cached_response(user_message: str) -> Optional[str]:
    """
    Retrieve cached response for a given user message.

    Args:
        user_message: The message to look up in cache.

    Returns:
        Optional[str]: The cached response if found, None otherwise.
    """
    cache_key = f"secure_chatbot_response_{hash_message(user_message)}"
    cached_response = cache.get(cache_key)
    logger.info('Cache %s for message: %s',
                'hit' if cached_response else 'miss', 
                user_message)
    return cached_response


def set_cached_response(user_message: str, response: str) -> None:
    """
    Cache the response for a given user message.

    Args:
        user_message: The message to use as cache key.
        response: The response to cache.
    """
    cache_key = f"secure_chatbot_response_{hash_message(user_message)}"
    cache.set(cache_key, response, timeout=200)


def detect_language(user_message: str) -> str:
    """
    Detect the language of the user's message.

    Args:
        user_message: The message to analyze.

    Returns:
        str: Language code ('sv' for Swedish, 'en' for English).
    """
    if len(user_message) <= 2:
        return "en"

    swedish_greetings: List[str] = [
        "hej", "hallå", "tjena", "hejsan",
        "hej!", "hallå!", "tjena!", "hejsan!",
    ]
    if user_message.lower() in swedish_greetings:
        logger.info('Detected Swedish via keyword matching: %s', user_message)
        return "sv"

    try:
        detected_languages = detect_langs(user_message)
        logger.info(
            'Language detection results for "%s": %s',
            user_message,
            detected_languages
        )

        for lang in detected_languages:
            if lang.lang == "sv" and lang.prob > 0.5:
                logger.info('Detected language: Swedish (%s)', lang.prob)
                return "sv"

    except (ValueError, TypeError) as e:
        logger.error('Language detection failed: %s', e)

    logger.info('Defaulting to English for message: %s', user_message)
    return "en"


@csrf_protect
@api_view(["POST"])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
@permission_classes([IsAuthenticatedOrReadOnly])
@ratelimit(key="ip", rate="5/m", block=True)
def chatbot(request):
    """
    Handle chatbot requests, providing responses from OpenAI API or cache.

    Args:
        request: The incoming HTTP request.

    Returns:
        Response: JSON response containing message or error.
    """
    user_message = request.data.get("message", "").strip()
    if not user_message:
        return Response(
            {"error": "Please enter a message to get a response."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    safe_user_message = escape(user_message)
    cached_response = get_cached_response(safe_user_message)
    if cached_response:
        return Response(
            {"message": cached_response},
            status=status.HTTP_200_OK
        )

    try:
        detected_language = detect_language(safe_user_message)
        logger.info('Detected language: %s', detected_language)

        system_prompt = _get_system_prompt(detected_language)
        response = _get_openai_response(safe_user_message, system_prompt)

        bot_message = response.choices[0].message.content.strip()
        set_cached_response(safe_user_message, bot_message)

        return Response({"message": bot_message}, status=status.HTTP_200_OK)

    except (APIError, RateLimitError, Timeout) as e:
        logger.error('OpenAI API error: %s', e)
        return Response(
            {"error": "Failed to process your request."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_system_prompt(language: str) -> str:
    """Get the appropriate system prompt based on language."""
    if language == "sv":
        return (
            "Du är en chatbot för Nordic Code Works. "
            "Vi bygger anpassade, högkvalitativa fullstack-webbapplikationer "
            "till rimliga priser. Du svarar ENDAST på frågor som rör våra "
            "tjänster, våra projekt och hur man kan starta ett projekt."
        )
    return (
        "You are a chatbot for Nordic Code Works. "
        "We build high-quality, custom full-stack web applications at "
        "competitive prices. You ONLY answer questions related to our "
        "services, our projects, and how to start a project."
    )


def _get_openai_response(message: str, system_prompt: str):
    """Get response from OpenAI API."""
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        max_tokens=150,
        temperature=0.3,
    )
