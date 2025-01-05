import logging

from django.conf import settings
from django.core.cache import cache
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from langdetect import detect_langs
from openai import APIError, OpenAI, RateLimitError, Timeout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .hash import hash_message

# Create your views here.


# OpenAI Client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

logger = logging.getLogger(__name__)


def get_cached_response(user_message: str) -> str:
    """Retrieve cached response for a given user message."""
    cache_key = f"secure_chatbot_response_{hash_message(user_message)}"
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"Cache hit for message: {user_message}")
    else:
        logger.info(f"Cache miss for message: {user_message}")
    return cached_response


def set_cached_response(user_message: str, response: str) -> None:
    """Cache the response for a given user message."""
    cache_key = f"secure_chatbot_response_{hash_message(user_message)}"
    cache.set(cache_key, response, timeout=200)


def detect_language(user_message: str) -> str:
    """
    Detect the language of the user's message.
    Uses langdetect's detect_langs() to get a list of possible languages and their probabilities.
    Defaults to Swedish if "hej" or common Swedish greetings are found.
    """
    if len(user_message) <= 2:
        return "en"

    swedish_greetings = [
        "hej",
        "hallå",
        "tjena",
        "hejsan",
        "hej!",
        "hallå!",
        "tjena!",
        "hejsan!",
    ]
    if user_message.lower() in swedish_greetings:
        logger.info(f"Detected Swedish via keyword matching: {user_message}")
        return "sv"

    try:
        detected_languages = detect_langs(user_message)
        logger.info(
            f"Language detection results for '{user_message}': {detected_languages}"
        )

        for lang in detected_languages:
            if lang.lang == "sv" and lang.prob > 0.5:
                logger.info(f"Detected language: Swedish ({lang.prob})")
                return "sv"

    except Exception as e:
        logger.error(f"Language detection failed: {e}")

    logger.info(f"Defaulting to English for message: {user_message}")
    return "en"


@csrf_protect
@api_view(["POST"])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
@permission_classes([IsAuthenticatedOrReadOnly])
@ratelimit(key="ip", rate="5/m", block=True)
def chatbot(request):
    """Handle chatbot requests, providing responses from OpenAI API or cache."""
    user_message = request.data.get("message", "").strip()
    if not user_message:
        return Response(
            {"error": "Please enter a message to get a response."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    safe_user_message = escape(user_message)
    cached_response = get_cached_response(safe_user_message)
    if cached_response:
        return Response({"message": cached_response}, status=status.HTTP_200_OK)

    try:

        detected_language = detect_language(safe_user_message)
        logger.info(f"Detected language: {detected_language}")

        if detected_language == "sv":
            system_prompt = (
                "Du är en chatbot för Nordic Code Works. "
                "Vi bygger anpassade, högkvalitativa fullstack-webbapplikationer till rimliga priser. "
                "Du svarar ENDAST på frågor som rör våra tjänster, våra projekt och hur man kan starta ett projekt. "
                "Om användaren ställer en orelaterad fråga, svarar du med: "
                "'Jag är här för att hjälpa till med frågor om våra projekt och hur du kan starta ett projekt med oss.' "
                "Om användaren verkar osäker, föreslå: 'Vill du veta hur vi kan hjälpa dig att bygga din nästa webbapplikation?'"
            )
        else:
            system_prompt = (
                "You are a chatbot for Nordic Code Works. "
                "We build high-quality, custom full-stack web applications at competitive prices. "
                "You ONLY answer questions related to our services, our projects, and how to start a project. "
                "If the user asks an unrelated question, reply with: "
                "'I'm here to help with questions about our projects and how you can start your own project with us.' "
                "If the user seems unsure, suggest: 'Would you like to learn how we can help you build your next web application?'"
            )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": safe_user_message},
            ],
            max_tokens=150,
            temperature=0.3,
        )

        bot_message = response.choices[0].message.content.strip()
        set_cached_response(safe_user_message, bot_message)

        return Response({"message": bot_message}, status=status.HTTP_200_OK)
    except (APIError, RateLimitError, Timeout) as e:
        logger.error(f"OpenAI API error: {e}")
        return Response(
            {"error": "Failed to process your request."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
