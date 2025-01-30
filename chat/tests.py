import pytest
from allauth.account.models import EmailAddress
from channels.testing import WebsocketCommunicator
from contacts.models import ProjectConversation, ProjectMessage
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.asgi import application
from projects.models import Project

User = get_user_model()


class ProjectConversationSignalTests(TestCase):
    """Test ProjectConversation signals."""

    def setUp(self):
        """Initialize user."""
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
        )

    def test_conversation_created_on_project_creation(self):
        """Ensure conversation is created."""
        project = Project.objects.create(
            user=self.user,
            title="Test Project",
            description="A test project.",
            status="in_progress",
        )
        self.assertTrue(ProjectConversation.objects.filter(project=project).exists())
        conversation = ProjectConversation.objects.get(project=project)
        self.assertEqual(conversation.project, project)

    def test_no_conversation_created_for_planning_status(self):
        """Ensure no conversation for planning."""
        project = Project.objects.create(
            user=self.user,
            title="Planning Project",
            description="A test project in planning.",
            status="planning",
        )
        self.assertFalse(ProjectConversation.objects.filter(project=project).exists())


@pytest.mark.django_db
class ContactsAppTests(APITestCase):
    """Test Contacts app API endpoints."""

    def setUp(self):
        """Initialize verified user, login, create project."""
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            is_verified=True,
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )
        login_resp = self.client.post(
            "/auth/login/",
            {"email": "testuser@example.com", "password": "testpassword123"},
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", login_resp.cookies)
        self.access_token = login_resp.cookies["access_token"].value
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.project = Project.objects.create(
            user=self.user,
            title="Test Project",
            description="A test project for messaging.",
            status="in_progress",
        )
        self.conversation = self.project.conversation
        self.conversations_list_url = reverse("contacts:conversations-list")
        self.conversation_detail_url = reverse(
            "contacts:conversations-detail",
            args=[self.conversation.id],
        )
        self.messages_list_url = reverse("contacts:messages-list")

    def tearDown(self):
        """Clean up data."""
        ProjectMessage.objects.all().delete()
        ProjectConversation.objects.all().delete()
        Project.objects.all().delete()
        EmailAddress.objects.all().delete()
        User.objects.all().delete()

    def test_authenticated_user_can_access_conversations(self):
        """Access conversation list."""
        resp = self.client.get(self.conversations_list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_unauthenticated_access_is_denied(self):
        """Unauthenticated access denied."""
        self.client.logout()
        if "access_token" in self.client.cookies:
            del self.client.cookies["access_token"]

        resp = self.client.get(self.conversations_list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_conversation_detail(self):
        """Retrieve conversation details."""
        resp = self.client.get(self.conversation_detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["project_title"], self.project.title)
        self.assertEqual(resp.data["client_name"], self.user.full_name)
        self.assertIn("messages", resp.data)
        self.assertEqual(len(resp.data["messages"]), 0)

    def test_mark_all_messages_as_read(self):
        """Mark messages as read."""
        msg1 = ProjectMessage.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Hello #1",
        )
        msg2 = ProjectMessage.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Hello #2",
        )
        self.assertFalse(msg1.read_by.exists())
        self.assertFalse(msg2.read_by.exists())
        mark_read_url = reverse(
            "contacts:conversations-mark-read",
            args=[self.conversation.id],
        )
        resp = self.client.post(mark_read_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg1.refresh_from_db()
        msg2.refresh_from_db()
        self.assertIn(self.user, msg1.read_by.all())
        self.assertIn(self.user, msg2.read_by.all())

    def test_create_message(self):
        """Create new message."""
        payload = {
            "conversation": self.conversation.id,
            "content": "Hello from a separate messages endpoint!",
        }
        resp = self.client.post(self.messages_list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_msg_id = resp.data["id"]
        self.assertTrue(ProjectMessage.objects.filter(id=new_msg_id).exists())
        msg_obj = ProjectMessage.objects.get(id=new_msg_id)
        self.assertEqual(msg_obj.content, payload["content"])
        self.assertEqual(msg_obj.sender, self.user)

    def test_message_attachment_validation(self):
        """Test file size/type validation for message attachments."""
        valid_file = SimpleUploadedFile(
            "test.pdf", b"dummy content", content_type="application/pdf"
        )
        payload = {
            "conversation": self.conversation.id,
            "content": "Message with valid attachment",
            "files": [valid_file],
        }
        response = self.client.post(self.messages_list_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = ProjectMessage.objects.first()
        self.assertIsNotNone(message)
        attachment = message.attachments.first()
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.file_name, "test.pdf")
        self.assertEqual(attachment.file_type, "application/pdf")

        self.client.logout()
        self.client.login(email="testuser@example.com", password="testpassword123")

        large_file = SimpleUploadedFile(
            "large_file.pdf",
            b"X" * (5 * 1024 * 1024 + 1),
            content_type="application/pdf",
        )
        payload["files"] = [large_file]
        response = self.client.post(self.messages_list_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.logout()
        self.client.login(email="testuser@example.com", password="testpassword123")

        invalid_file_ext = SimpleUploadedFile(
            "test.exe", b"dummy content", content_type="application/octet-stream"
        )
        payload["files"] = [invalid_file_ext]
        response = self.client.post(self.messages_list_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @pytest.mark.asyncio
    async def test_websocket_communication(self):
        """Test WebSocket."""
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.conversation.id}/"
        )
        communicator.scope["user"] = self.user
        connected, subprotocol = await communicator.connect()
        assert connected is True
        await communicator.send_json_to({"message": "Hello WebSocket!"})
        response = await communicator.receive_json_from()
        assert response["message"] == "Hello WebSocket!"
        await communicator.disconnect()
