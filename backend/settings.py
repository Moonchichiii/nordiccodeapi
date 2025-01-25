"""
Nordic Code Works Django Settings

This module contains all Django settings for the Nordic Code Works project,
organized by functionality and purpose.
"""

from datetime import timedelta
from pathlib import Path
import dj_database_url
from decouple import config
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

# =============================================================================
# CORE DJANGO CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_NAME = "Nordic Code Works"
ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = config("SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

# Security Headers and Options
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "django_extensions",
    "corsheaders",
    "cloudinary",
    "cloudinary_storage",
    "django_ratelimit",
    "django_filters",
    "channels",
    "csp",
]

LOCAL_APPS = [
    "users",
    "projects",
    "planner",
    "chat",
    "chatbot",
    "orders",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    #  Testing "django_ratelimit.middleware.RatelimitMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

# =============================================================================
# TEMPLATES CONFIGURATION
# =============================================================================

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

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

AUTH_USER_MODEL = "users.CustomUser"
SITE_ID = 1
APPEND_SLASH = False

AUTHENTICATION_BACKENDS = [
    "users.auth_backends.CaseInsensitiveEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# AllAuth Settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = f"{FRONTEND_URL}/email-verified"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = f"{FRONTEND_URL}/email-verified"

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=12),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "email",
    "USER_ID_CLAIM": "email",
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_REFRESH": "refresh_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax",
    "AUTH_COOKIE_SECURE": not DEBUG
}

# =============================================================================
# REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": SIMPLE_JWT["AUTH_COOKIE"],
    "JWT_AUTH_REFRESH_COOKIE": SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
    "JWT_AUTH_HTTPONLY": SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
    "JWT_AUTH_SAMESITE": SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
    "JWT_AUTH_SECURE": SIMPLE_JWT["AUTH_COOKIE_SECURE"],
    "USER_DETAILS_SERIALIZER": "users.serializers.CustomUserDetailsSerializer",
    "LOGIN_SERIALIZER": "users.serializers.CustomLoginSerializer",
    "SESSION_LOGIN": False,
}

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = 'backend.backends.gmail.GmailOAuth2Backend' if not DEBUG else 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')
SERVER_EMAIL = config('SERVER_EMAIL', default=EMAIL_HOST_USER)

# OAuth2 Settings
GOOGLE_OAUTH2_CLIENT_ID = config('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = config('GOOGLE_OAUTH2_CLIENT_SECRET')
GOOGLE_OAUTH2_REFRESH_TOKEN = config('GOOGLE_OAUTH2_REFRESH_TOKEN')

# =============================================================================
# SOCIAL AUTH CONFIGURATION
# =============================================================================

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': GOOGLE_OAUTH2_CLIENT_ID,
            'secret': GOOGLE_OAUTH2_CLIENT_SECRET,
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
            'openid',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
            'prompt': 'select_account consent',
        },
        'VERIFIED_EMAIL': True,
        'CALLBACK_URL': f"{FRONTEND_URL}/auth/google/callback/",
        'FETCH_EXTRA_DATA': [
            ('given_name', 'first_name'),
            ('family_name', 'last_name'),
            ('picture', 'profile_picture'),
            ('locale', 'language'),
        ],
        'EXCHANGE_TOKEN': True,
        'ENABLED': True,
        'OAUTH_PKCE_ENABLED': True,
    }
}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    "default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC AND MEDIA FILES CONFIGURATION
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

MEDIA_FILE_STORAGE = {
    "max_upload_size": 5242880,
    "allowed_extensions": ["pdf", "doc", "docx", "jpg", "png", "svg"],
}

# Cloudinary Settings
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
}

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# =============================================================================
# THIRD-PARTY SERVICES CONFIGURATION
# =============================================================================

# API Keys
IDEAL_POSTCODES_API_KEY = config("IDEAL_POSTCODES_API_KEY")
DEUTSCHE_POST_API_KEY = config("DEUTSCHE_POST_API_KEY")
LA_POSTE_API_KEY = config("LA_POSTE_API_KEY")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY")
OPENAI_API_KEY = config("OPENAI_API_KEY")

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    'https://accounts.google.com',
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "https://nordiccodeworks.com",
]

# =============================================================================
# CACHING AND REDIS CONFIGURATION
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "RETRY_ON_TIMEOUT": True,
            "CONNECTION_POOL_CLASS": "redis.connection.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
        }
    }
}

# Add fallback cache for when Redis is down
CACHES["backup"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "fallback",
}
PACKAGE_CACHE_TIMEOUT = 60 * 15

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================

RATELIMIT_ENABLE = False
RATELIMIT_VIEW = "django_ratelimit.views.ratelimited"
RATELIMIT_CACHE = "default"
RATELIMIT_GROUPS = {"default": {"rate": "10/m"}}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

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

# =============================================================================
# CONTENT SECURITY POLICY
# =============================================================================

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
    'https://accounts.google.com',
)
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
OBJECT_SRC = ("'none'",)


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
# Default Field Type
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
