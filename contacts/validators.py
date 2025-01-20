import os

from django.core.exceptions import ValidationError


def validate_file_size(file):
    """Validate that the file size is less than or equal to 5MB."""
    max_size = 5 * 1024 * 1024  # 5MB
    print(f"File Size: {file.size}")  # Debug: Log file size
    if file.size > max_size:
        raise ValidationError(
            f"File size must not exceed {max_size / (1024 * 1024)}MB."
        )


def validate_file_extension(file):
    """Validate that the file has an allowed extension."""
    allowed_extensions = [".pdf", ".jpeg", ".png", ".jpg"]
    ext = os.path.splitext(file.name)[1].lower()
    print(f"File Extension: {ext}")  # Debug: Log file extension
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Invalid file type. Only the following file types are allowed: {', '.join(allowed_extensions)}"
        )
