from django.core.exceptions import ValidationError
from django.conf import settings

def validate_file_size(value):
    max_size = settings.MEDIA_FILE_STORAGE['max_upload_size']
    if value.size > max_size:
        raise ValidationError(f'File size cannot exceed {max_size/1024/1024}MB')

def validate_file_extension(value):
    allowed_extensions = settings.MEDIA_FILE_STORAGE['allowed_extensions']
    ext = value.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'File type .{ext} is not supported')