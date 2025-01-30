import os

from django.core.exceptions import ValidationError


def validate_file_size(file) -> None:
    """Validate that the file size is <= 5MB.

    Args:
        file: The file to validate.

    Raises:
        ValidationError: If the file size exceeds 5MB.
    """
    max_size = 5 * 1024 * 1024
    print(f"File Size: {file.size}")
    if file.size > max_size:
        raise ValidationError(
            f"File size must not exceed {max_size / (1024 * 1024)}MB."
        )


def validate_file_extension(file) -> None:
    """Validate that the file has an allowed extension.

    Args:
        file: The file to validate.

    Raises:
        ValidationError: If the file extension is not allowed.
    """
    allowed_extensions = [".pdf", ".jpeg", ".png", ".jpg"]
    ext = os.path.splitext(file.name)[1].lower()
    print(f"File Extension: {ext}")
    if ext not in allowed_extensions:
        raise ValidationError(
            "Invalid file type. Only the following file types are allowed: "
            f"{', '.join(allowed_extensions)}"
        )
