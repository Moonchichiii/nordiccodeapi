"""
This module provides functions to hash and verify messages 
and secrets using HMAC-SHA256 and SHA-256.
Functions:
    hash_message(message: str) -> str:
        Hash the user's message using 
        HMAC-SHA256 with an optional pepper for enhanced security.
    hash_secret(secret: str, salt: str = None) -> str:
        Hash a secret (like an API key or password) 
        using SHA-256 with an optional salt for enhanced security.
    verify_message_hash(message: str, message_hash: str) -> bool:
        Verify if the provided message matches its hash using HMAC-SHA256.
"""

import hashlib
import hmac
import os

# Optional: Pepper value to make the hash even more secure (add it via environment variable)
PEPPER = os.getenv("HASH_PEPPER", "default_pepper_value")


def hash_message(message: str) -> str:
    """
    Hash the user's message using HMAC-SHA256.
    Uses a PEPPER to enhance security (useful if a database is compromised).
    Args:
        message (str): The message to hash.
    Returns:
        str: A SHA-256 hash of the message.
    """
    if not isinstance(message, str):
        raise ValueError("Message must be a string.")

    # Use HMAC to combine the message with a pepper (extra layer of security)
    message_bytes = message.encode("utf-8")
    pepper_bytes = PEPPER.encode("utf-8")

    # HMAC SHA-256 hashing
    message_hash = hmac.new(pepper_bytes, message_bytes, hashlib.sha256).hexdigest()
    return message_hash


def hash_secret(secret: str, salt: str = None) -> str:
    """
    Hash a secret (like an API key or password) using SHA-256.
    You can provide a salt to make it more secure.
    Args:
        secret (str): The secret to hash.
        salt (str, optional): Optional salt to add to the hash.
    Returns:
        str: A SHA-256 hash of the secret.
    """
    if not isinstance(secret, str):
        raise ValueError("Secret must be a string.")

    if salt is None:
        # Generate a random salt if not provided (16 random bytes)
        salt = os.urandom(16).hex()

    # Hash the secret combined with the salt
    secret_bytes = f"{secret}{salt}".encode("utf-8")
    secret_hash = hashlib.sha256(secret_bytes).hexdigest()
    return secret_hash


def verify_message_hash(message: str, message_hash: str) -> bool:
    """
    Verify if the provided message matches its hash.
    Args:
        message (str): The original message.
        message_hash (str): The hashed value of the message.
    Returns:
        bool: True if the message matches the hash, False otherwise.
    """
    if not isinstance(message, str) or not isinstance(message_hash, str):
        raise ValueError("Both message and message_hash must be strings.")

    calculated_hash = hash_message(message)
    return hmac.compare_digest(calculated_hash, message_hash)
