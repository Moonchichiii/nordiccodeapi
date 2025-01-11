import pytest
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from projects.models import Project
from contacts.models import ProjectConversation, ProjectMessage
from allauth.account.models import EmailAddress
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from backend.asgi import application

User = get_user_model()

class ContactsAppTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            is_verified=True,
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )
        response = self.client.post(
            '/auth/login/',
            {"email": "testuser@example.com", "password": "testpassword123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)
        self.access_token = response.cookies["access_token"].value
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.project = Project.objects.create(
            user=self.user,
            title="Test Project",
            description="A test project for messaging.",
            status="in_progress",
        )
        self.conversation = self.project.conversation

    def tearDown(self):
        ProjectMessage.objects.all().delete()
        ProjectConversation.objects.all().delete()
        Project.objects.all().delete()
        EmailAddress.objects.all().delete()
        User.objects.all().delete()

    def test_authenticated_user_access(self):
        response = self.client.get(reverse("project-messages-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        self.client.credentials()
        response = self.client.get(reverse("project-messages-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_conversation_creation_signal(self):
        project = Project.objects.create(
            user=self.user, title="Another Project", status="in_progress"
        )
        conversation_exists = ProjectConversation.objects.filter(project=project).exists()
        self.assertTrue(conversation_exists)

    def test_get_conversation_list(self):
        url = reverse("project-messages-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        conversation_data = response.data['results'][0]
        self.assertEqual(conversation_data["project_title"], self.project.title)

    def test_send_message(self):
        url = f"{reverse('project-messages-detail', args=[self.conversation.id])}send-message/"
        data = {"content": "Hello Admin!"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = ProjectMessage.objects.first()
        self.assertEqual(message.content, "Hello Admin!")
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.conversation, self.conversation)

    def test_mark_message_as_read(self):
        message = ProjectMessage.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Hello!"
        )
        self.assertNotIn(self.user, message.read_by.all())
        url = f"{reverse('project-messages-detail', args=[self.conversation.id])}mark-read/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertIn(self.user, message.read_by.all())

    def test_get_conversation_detail(self):
        url = reverse("project-messages-detail", args=[self.conversation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["project_title"], self.project.title)
        self.assertEqual(response.data["client_name"], self.user.full_name)

@pytest.mark.asyncio
async def test_websocket_communication(self):
    communicator = WebsocketCommunicator(
        application, f"/ws/chat/{self.conversation.id}/"
    )
    communicator.scope["user"] = self.user
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({"message": "Hello WebSocket!"})
    response = await communicator.receive_json_from()
    assert response["message"] == "Hello WebSocket!"
    await communicator.disconnect()

def test_message_attachment_validation(self):
    file_data = SimpleUploadedFile(
        "test.pdf", b"dummy content", content_type="application/pdf"
    )
    url = reverse("project-messages-detail", args=[self.conversation.id]) + "send-message/"
    response = self.client.post(
        url,
        {
            "content": "Attached file",
            "attachments": [{"file": file_data, "file_name": "test.pdf"}],
        },
        format="multipart",
    )
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    attachment = ProjectMessage.objects.first().attachments.first()
    self.assertEqual(attachment.file_name, "test.pdf")
