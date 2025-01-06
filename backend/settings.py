"""Django settings module for the Nordic Code Works project.

This module contains all the settings and configurations for the Django project,
including security, database, authentication, and third-party integrations.
"""

import sys
from pathlib import Path

import dj_database_url
from decouple import config
from datetime import timedelta


# Paths configuration
BASE_DIR = Path(__file__).resolve().parent.parent


# Security settings
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

PROJECT_NAME = "Nordic Code Works"

if "test" in sys.argv:
    CSRF_TRUSTED_ORIGINS = ["http://testserver"]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",    
    "allauth.socialaccount",    
    "allauth.socialaccount.providers.google",    
    "rest_framework.authtoken",    
    "rest_framework_simplejwt",    
    "dj_rest_auth",    
    "dj_rest_auth.registration",       
    "rest_framework",    
    "corsheaders",
    "cloudinary",
    "cloudinary_storage",
    "django_ratelimit",
    "django_filters",
    "csp",
    "users",
    "contacts",
    "projects",
    "chatbot",
    "orders",
]


SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": "YOUR_GOOGLE_CLIENT_ID",
            "secret": "YOUR_GOOGLE_CLIENT_SECRET",
            "key": "",
        }
    }
}

# Authentication settings
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

AUTH_USER_MODEL = "users.CustomUser"


# Middleware configuration
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database configuration
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        )
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static and media files configuration
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cloudinary configuration
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
}

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

MEDIA_FILE_STORAGE = {
    'max_upload_size': 5242880,
    'allowed_extensions': ['pdf', 'doc', 'docx', 'jpg', 'png', 'svg'],
}

# Stripe configuration
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY")


# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

REST_AUTH_TOKEN_MODEL = None

REST_AUTH_SERIALIZERS = {
    "LOGIN_SERIALIZER": "dj_rest_auth.serializers.LoginSerializer",
    "JWT_SERIALIZER": "dj_rest_auth.serializers.JWTSerializer",
}

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "users.serializers.CustomRegisterSerializer",
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_COOKIE": "access_token",  
    "AUTH_COOKIE_HTTP_ONLY": True, 
    "AUTH_COOKIE_SECURE": False,   
    "AUTH_COOKIE_SAMESITE": "Lax", 
}

# OpenAI configuration
OPENAI_API_KEY = config("OPENAI_API_KEY")

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://nordiccodeworks.com",
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173"]

# Security settings for development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# Redis and caching configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

# Rate limiting configuration
RATELIMIT_ENABLE = True
RATELIMIT_VIEW = "django_ratelimit.views.ratelimited"
RATELIMIT_CACHE = "default"
RATELIMIT_GROUPS = {"default": {"rate": "10/m"}}

# Celery configuration
CELERY_BROKER_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://127.0.0.1:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "max_retries": 3,
    "interval_start": 0,
    "interval_step": 0.2,
    "interval_max": 0.5,
}

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Content Security Policy configuration
CSP_DEFAULT_SRC = ("'self'", "http://localhost:5173")
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://cdnjs.cloudflare.com",
    "http://localhost:5173",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "http://localhost:5173",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "blob:",
    "https://res.cloudinary.com",
    "http://localhost:8000",
    "http://localhost:5173",
)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "data:")
CSP_CONNECT_SRC = (
    "'self'",
    "http://localhost:8000",
    "http://localhost:5173",
    "https://nordiccodeworks.com",
    "https://api.openai.com",
)
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)

# Default field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(levelname)s] %(asctime)s %(module)s %(message)s",
            "style": "%",
        },
        "simple": {
            "format": "[%(levelname)s] %(message)s",
            "style": "%",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "error.log",
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": True,
        },
        "contact": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
