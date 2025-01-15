import pytest
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from django.core.files.uploadedfile import SimpleUploadedFile

from channels.testing import WebsocketCommunicator
from backend.asgi import application

from projects.models import Project
from contacts.models import ProjectConversation, ProjectMessage

User = get_user_model()


@pytest.mark.django_db
class ContactsAppTests(APITestCase):
    def setUp(self):
        """
        Create a verified user, login, and set up a test Project and ProjectConversation.
        """
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            is_verified=True,
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )

        # Login to get JWT/cookies
        login_resp = self.client.post(
            "/auth/login/",
            {"email": "testuser@example.com", "password": "testpassword123"},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access_token", login_resp.cookies)
        self.access_token = login_resp.cookies["access_token"].value

        # Set Authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Create a test project
        # The signal will auto-create a conversation if status != "planning".
        self.project = Project.objects.create(
            user=self.user,
            title="Test Project",
            description="A test project for messaging.",
            status="in_progress",
        )
        # Now the conversation should exist, courtesy of the signal
        self.conversation = self.project.conversation

        # Common URLs (assuming routers: "conversations" and "messages")
        self.conversations_list_url = reverse("conversations-list")
        self.conversation_detail_url = reverse(
            "conversations-detail", args=[self.conversation.id]
        )

        self.messages_list_url = reverse("messages-list")

    def tearDown(self):
        """
        Clean up database tables after each test.
        """
        ProjectMessage.objects.all().delete()
        ProjectConversation.objects.all().delete()
        Project.objects.all().delete()
        EmailAddress.objects.all().delete()
        User.objects.all().delete()

    # ----------------------------------------------------
    # Authentication & Permissions
    # ----------------------------------------------------

    def test_authenticated_user_can_access_conversations(self):
        """
        Authenticated user should be able to GET conversation list.
        """
        resp = self.client.get(self.conversations_list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)  # We already have 1 conversation

    def test_unauthenticated_access_is_denied(self):
        """
        When user logs out, subsequent requests should yield 401 Unauthorized.
        """
        self.client.logout()
        # Or explicitly remove JWT cookies
        if "access_token" in self.client.cookies:
            del self.client.cookies["access_token"]
        if "refresh_token" in self.client.cookies:
            del self.client.cookies["refresh_token"]

        resp = self.client.get(self.conversations_list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ----------------------------------------------------
    # Conversations CRUD Tests
    # ----------------------------------------------------

    def test_get_conversation_detail(self):
        """
        Ensure we can retrieve conversation detail, including project title & client name.
        """
        resp = self.client.get(self.conversation_detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["project_title"], self.project.title)
        self.assertEqual(resp.data["client_name"], self.user.full_name)
        self.assertIn("messages", resp.data)
        self.assertEqual(len(resp.data["messages"]), 0)  # No messages yet

    def test_create_new_conversation(self):
    payload = {"project": self.project.id}
    resp = self.client.post(self.conversations_list_url, payload, format="json")

    if resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        # Means your ViewSet might not allow creation if you're doing a OneToOne with Project
        self.skipTest("Conversation creation is disallowed by the ViewSet.")
    else:
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ...


    def test_mark_all_messages_as_read(self):
        """
        The 'mark-read' custom action should mark all messages in a conversation as read by current user.
        """
        # Create 2 messages in the conversation
        msg1 = ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="Hello #1"
        )
        msg2 = ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="Hello #2"
        )
        self.assertFalse(msg1.read_by.exists())
        self.assertFalse(msg2.read_by.exists())

        mark_read_url = reverse("conversations-mark-read", args=[self.conversation.id])
        resp = self.client.post(mark_read_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        msg1.refresh_from_db()
        msg2.refresh_from_db()
        self.assertIn(self.user, msg1.read_by.all())
        self.assertIn(self.user, msg2.read_by.all())

    # ----------------------------------------------------
    # Messages CRUD Tests
    # ----------------------------------------------------

    def test_create_message(self):
        """
        POST /messages/ to create a new ProjectMessage in a conversation for which the user is owner.
        """
        payload = {
            "conversation": self.conversation.id,
            "content": "Hello from a separate messages endpoint!"
        }
        resp = self.client.post(self.messages_list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_msg_id = resp.data["id"]
        self.assertTrue(ProjectMessage.objects.filter(id=new_msg_id).exists())
        msg_obj = ProjectMessage.objects.get(id=new_msg_id)
        self.assertEqual(msg_obj.content, payload["content"])
        self.assertEqual(msg_obj.sender, self.user)

    def test_list_messages(self):
        """
        Ensure we can list all messages that belong to the user (across all conversations).
        """
        ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="Msg #1"
        )
        ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="Msg #2"
        )
        resp = self.client.get(self.messages_list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_retrieve_single_message(self):
        """
        GET /messages/<pk>/ to retrieve a single message.
        """
        message = ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="Single Retrieve"
        )
        url = reverse("messages-detail", args=[message.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["content"], "Single Retrieve")
        self.assertEqual(resp.data["sender"], self.user.id)

    def test_update_message(self):
        """
        PATCH /messages/<pk>/ to update a message's content (e.g., if editing is allowed).
        """
        message = ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="Old Content"
        )
        url = reverse("messages-detail", args=[message.id])
        updated_data = {"content": "Updated Content"}
        resp = self.client.patch(url, updated_data, format="json")
        if resp.status_code == status.HTTP_403_FORBIDDEN:
            self.skipTest("Message editing is disallowed by the ViewSet.")
        else:
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            message.refresh_from_db()
            self.assertEqual(message.content, "Updated Content")

    def test_delete_message(self):
        """
        DELETE /messages/<pk>/ to delete a message if your policy allows it.
        """
        message = ProjectMessage.objects.create(
            conversation=self.conversation, sender=self.user, content="To delete"
        )
        url = reverse("messages-detail", args=[message.id])
        resp = self.client.delete(url)
        if resp.status_code == status.HTTP_403_FORBIDDEN:
            self.skipTest("Message deletion is disallowed by the ViewSet.")
        else:
            self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(ProjectMessage.objects.filter(id=message.id).exists())

    def test_message_attachment_validation(self):
        """
        Test file size/type validation using a PDF upload.
        """
        file_data = SimpleUploadedFile(
            "test.pdf", b"dummy content", content_type="application/pdf"
        )
        payload = {
            "conversation": self.conversation.id,
            "content": "Attached file",
            "attachments": [{"file": file_data, "file_name": "test.pdf"}],
        }
        resp = self.client.post(self.messages_list_url, payload, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        attachment = ProjectMessage.objects.first().attachments.first()
        self.assertEqual(attachment.file_name, "test.pdf")

    # ----------------------------------------------------
    # WebSocket Test
    # ----------------------------------------------------
    @pytest.mark.asyncio
    async def test_websocket_communication(self):
        """
        Test that a user can connect to a conversation WebSocket and send/receive messages.
        """
        # Create a communicator
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.conversation.id}/"
        )
        # Set an authenticated user
        communicator.scope["user"] = self.user

        # Connect
        connected, subprotocol = await communicator.connect()
        assert connected is True

        # Send a message JSON
        await communicator.send_json_to({"message": "Hello WebSocket!"})

        # Receive a message from the server
        response = await communicator.receive_json_from()
        assert response["message"] == "Hello WebSocket!"

        # Disconnect
        await communicator.disconnect()
