"""
Nordic Code Works Django Settings

This module contains all Django settings for the Nordic Code Works project,
organized by functionality and purpose.
"""

from datetime import timedelta
from pathlib import Path
import dj_database_url
from decouple import config
from .google import GoogleService
from django.templatetags.static import static

google_service = GoogleService()
google_config = google_service.get_config()

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
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",    
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
    "billing",
    "planner",
    "chat",
    
    "chatbot",    
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

UNFOLD = {
    "STYLES": [
         lambda request: static("css/admin.css"),
    ],
    "SITE_TITLE": "Nordic Code Works",
    "SITE_HEADER": "Site Management",
    "SITE_URL": "/",
    "SITE_ICON": None,
    "COLORS": {
        "primary": {
            "50": "#f8fafc",
            "100": "#f1f5f9",
            "200": "#e2e8f0",
            "300": "#cbd5e1",
            "400": "#94a3b8",
            "500": "#64748b",
            "600": "#475569",
            "700": "#334155",
            "800": "#1e293b",
            "900": "#0f172a",
        },
        "secondary": {
            "50": "#f0f9ff",
            "100": "#e0f2fe",
            "200": "#bae6fd",
            "300": "#7dd3fc",
            "400": "#38bdf8",
            "500": "#0ea5e9",
            "600": "#0284c7",
            "700": "#0369a1",
            "800": "#075985",
            "900": "#0c4a6e",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "items": [
            {
                "title": "Users",
                "icon": "people",
                "items": [
                    {"title": "Users", "url": "admin:users_customuser_changelist"}
                ]
            },
            {
                "title": "Projects",
                "icon": "work",
                "items": [
                    {"title": "Projects", "url": "admin:projects_project_changelist"},
                    {"title": "Packages", "url": "admin:projects_projectpackage_changelist"}
                ]
            },
            {
                "title": "Billing",
                "icon": "payments",
                "items": [
                    {"title": "Payments", "url": "admin:billing_payment_changelist"},
                    {"title": "Plans", "url": "admin:billing_paymentplan_changelist"}
                ]
            }
        ]
    }
}



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
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""

# Email Verification URLs - Single source of truth
ACCOUNT_EMAIL_CONFIRMATION_URL = "verify-email"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = f"{FRONTEND_URL}/email-verified"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = f"{FRONTEND_URL}/email-verified"

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=12),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_REFRESH": "refresh_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax",
    "AUTH_COOKIE_SECURE": not DEBUG,
    "USER_EMAIL_FIELD": "email",
    "USER_EMAIL_CLAIM": "email",
    "CLAIMS_MAPPING": {
        "id": "user_id",
        "email": "email",
        "is_staff": "is_staff",
        "is_verified": "is_verified"
    }
}

# REST Framework and Auth Configuration
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
    "REGISTER_SERIALIZER": "users.serializers.CustomRegisterSerializer",
    "SESSION_LOGIN": False,
    "OLD_PASSWORD_FIELD_ENABLED": True,
    "PASSWORD_RESET_USE_SITES_DOMAIN": False,
}

ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"
# Email Configuration
EMAIL_BACKEND = 'backend.google.GmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contact@nordiccodeworks.com'
DEFAULT_FROM_EMAIL = 'Nordic Code Works <contact@nordiccodeworks.com>'

# Google OAuth2 Configuration 
GOOGLE_OAUTH2_CLIENT_ID = google_config['GOOGLE_OAUTH2_CLIENT_ID']
GOOGLE_OAUTH2_CLIENT_SECRET = google_config['GOOGLE_OAUTH2_CLIENT_SECRET']
GOOGLE_OAUTH2_REFRESH_TOKEN = google_config['GOOGLE_OAUTH2_REFRESH_TOKEN']

# Social Auth Configuration - Use config directly, no duplication
SOCIALACCOUNT_PROVIDERS = google_config['SOCIALACCOUNT_PROVIDERS']

# Email Rate Limits
EMAIL_RATE_LIMIT = {
    "verify_email": "3/h",
    "password_reset": "3/h",
}

ADDRESS_VALIDATION = {
    'NOMINATIM_USER_AGENT': f'{PROJECT_NAME}/1.0',
    'CACHE_TIMEOUT': 86400,
    'RATE_LIMIT': {
        'NOMINATIM': 1,
    }
}

if DEBUG:
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None
    CORS_ALLOW_CREDENTIALS = True

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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# File upload configuration
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

MEDIA_FILE_STORAGE = {
    "max_upload_size": 5242880,
    "allowed_extensions": ["pdf", "doc", "docx", "jpg", "png", "svg"],
}

STATICFILES_CONTENT_TYPES = {
    'js': 'application/javascript',
    'css': 'text/css',
    'woff2': 'font/woff2'
}

# Cloudinary configuration
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

AI_PLANNER = config("AI_PLANNER")

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

# =============================================================================
# CONTENT SECURITY POLICY
# =============================================================================

CSP_DEFAULT_SRC = (
    "'self'",
    "http://localhost:5173",
    "http://localhost:8000"
)

CSP_CONNECT_SRC = (
    "'self'",
    "ws://localhost:5173",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://api.anthropic.com",
    "https://160.79.104.0/23",
)

CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-eval'",
    "http://localhost:5173",
    "http://localhost:8000"
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://fonts.googleapis.com"
)


CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://res.cloudinary.com",
    "http://localhost:5173",
    "http://localhost:8000"
)

CSP_FONT_SRC = (
    "'self'", 
    "https://fonts.gstatic.com", 
    "data:"
)

CSP_FRAME_SRC = (
    "'self'",
    "http://localhost:5173",
    "http://localhost:8000"
)

CSP_FRAME_ANCESTORS = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

