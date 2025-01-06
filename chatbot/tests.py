"""Test module for chatbot functionality in the Nordic Code API.

This module contains test cases for the chatbot endpoint, including tests for
both valid and invalid requests.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_chatbot_no_message():
    """Test chatbot endpoint behavior when no message is provided.

    Verifies that the API returns a 400 status code and an error message when
    the request body is empty.
    """
    client = APIClient()
    url = reverse("chatbot")
    response = client.post(url, {}, format="json")
    data = response.json()

    assert response.status_code == 400
    assert "error" in data


@pytest.mark.django_db
def test_chatbot_with_message(mocker):
    """Test chatbot endpoint behavior with a valid message.

    Args:
        mocker: pytest-mock fixture for mocking OpenAI API calls

    Verifies that the API returns a 200 status code and a response message
    when given a valid input message.
    """
    client = APIClient()
    url = reverse("chatbot")

    mock_response = {"choices": [{"text": "Mocked response"}]}
    mocker.patch("openai.Completion.create", return_value=mock_response)

    request_data = {"message": "Hello chatbot!"}
    response = client.post(url, request_data, format="json")
    resp_data = response.json()

    assert response.status_code == 200
    assert "message" in resp_data
