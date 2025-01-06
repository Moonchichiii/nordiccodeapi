"""
Module for handling contact-related database models in the Nordic Code API.

This module defines the Contact model for storing and managing contact messages
from users.
"""

from django.db import models


class Contact(models.Model):
    """
    Model representing a contact message from users.

    Attributes:
        name (str): The name of the person sending the message
        email (str): The email address of the sender
        message (str): The content of the contact message
        created_at (datetime): Timestamp of message creation
    """

    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for the Contact model."""
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """
        Return a string representation of the Contact instance.

        Returns:
            str: Contact information in the format 'name - email'
        """
        return f"{self.name} - {self.email}"
