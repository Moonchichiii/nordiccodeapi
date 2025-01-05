import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_chatbot_no_message():
    client = APIClient()
    url = reverse("chatbot")
    response = client.post(url, {}, format="json")
    data = response.json()

    assert response.status_code == 400
    assert "error" in data


@pytest.mark.django_db
def test_chatbot_with_message(mocker):
    client = APIClient()
    url = reverse("chatbot")

    mocker.patch(
        "openai.Completion.create",
        return_value={"choices": [{"text": "Mocked response"}]},
    )

    data = {"message": "Hello chatbot!"}
    response = client.post(url, data, format="json")
    resp_data = response.json()

    assert response.status_code == 200
    assert "message" in resp_data
