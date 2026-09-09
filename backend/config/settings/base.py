from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third Party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "cloudinary",
    "cloudinary_storage",
    "django_extensions",
    # Local Apps
    "apps.common",
    "apps.accounts",
    "apps.organizations",
    "apps.brand_assets",
    "apps.social_accounts",
    "apps.content_planner",
    "apps.posts",
    "apps.scheduler",
    "apps.insights",
    "apps.reports",
    "apps.ai",
    "apps.notifications",
    "apps.plans",
    # "apps.integrations.meta",
    "apps.integrations.meta.apps.MetaIntegrationConfig",
]

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config("DB_NAME"),
#         "USER": config("DB_USER"),
#         "PASSWORD": config("DB_PASSWORD"),
#         "HOST": config("DB_HOST"),
#         "PORT": config("DB_PORT", cast=int),
#     }
# }

DATABASES = {"default": dj_database_url.config(default=config("DATABASE_URL"))}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "apps.common.exception_handler.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

SPECTACULAR_SETTINGS = {
    "TITLE": "Digital Marketing Platform API",
    "DESCRIPTION": "Production API",
    "VERSION": "1.0.0",
}

# ============================================================
# CELERY
# ============================================================

CELERY_BROKER_URL = config(
    "CELERY_BROKER_URL",
)

CELERY_RESULT_BACKEND = config(
    "CELERY_RESULT_BACKEND",
)

CELERY_ACCEPT_CONTENT = [
    "json",
]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = TIME_ZONE

CELERY_ENABLE_UTC = True

CELERY_TASK_TRACK_STARTED = True

CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60

# ============================================================
# CELERY BEAT
# ============================================================

CELERY_BEAT_SCHEDULE = {
    "activate-scheduled-subscriptions": {
        "task": ("apps.organizations.tasks." "activate_scheduled_subscriptions_task"),
        "schedule": 60.0,
    },
    "send-plan-expiry-reminders": {
        "task": ("apps.organizations.tasks." "send_plan_expiry_reminders_task"),
        "schedule": 3600.0,
    },
    "expire-due-subscriptions": {
        "task": ("apps.organizations.tasks." "expire_due_subscriptions_task"),
        "schedule": 3600.0,
    },
}


# ============================================================
# DJANGO CACHE
# ============================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config(
            "DJANGO_CACHE_REDIS_URL",
        ),
        "OPTIONS": {
            "db": 2,
        },
    },
}
# ============================================================
# META
# ============================================================

META_APP_ID = config(
    "META_APP_ID",
)

META_APP_SECRET = config(
    "META_APP_SECRET",
)

META_GRAPH_API_VERSION = config(
    "META_GRAPH_API_VERSION",
    default="v26.0",
)

META_OAUTH_REDIRECT_URI = config(
    "META_OAUTH_REDIRECT_URI",
    default="",
)

# Facebook Login for Business configuration.
#
# Current Meta configuration:
#   - General login variation
#   - System-user access token
#   - Never expiration
#   - Pages asset
#   - Instagram accounts asset
#   - Business Portfolio based authorization
#
# Keep this configuration ID aligned with the Meta Developer
# Dashboard configuration.
META_BUSINESS_LOGIN_CONFIG_ID = config(
    "META_BUSINESS_LOGIN_CONFIG_ID",
    default="",
)

# Fernet key used to encrypt Meta access tokens before
# persisting them in the database.
META_CREDENTIAL_ENCRYPTION_KEY = config(
    "META_CREDENTIAL_ENCRYPTION_KEY",
)

# HTTP timeout for Meta Graph API requests.
META_HTTP_TIMEOUT_SECONDS = config(
    "META_HTTP_TIMEOUT_SECONDS",
    default=30,
    cast=int,
)

FRONTEND_URL = config(
    "FRONTEND_URL",
    default="http://localhost:5173",
)
# ============================================================
# GROQ AI
# ============================================================

GROQ_API_KEY = config("GROQ_API_KEY")
GROQ_MODEL = config("GROQ_MODEL")


# ============================================================
# BREVO
# ============================================================

BREVO_API_KEY = config(
    "BREVO_API_KEY",
)

BREVO_SENDER_EMAIL = config(
    "BREVO_SENDER_EMAIL",
)

BREVO_SENDER_NAME = config(
    "BREVO_SENDER_NAME",
    default="Digital Marketing Platform",
)

# ------------------------------------------------------------
# Transactional Email Templates
# ------------------------------------------------------------

BREVO_TEMPLATE_WELCOME = config(
    "BREVO_TEMPLATE_WELCOME",
    cast=int,
)

BREVO_TEMPLATE_EXPIRY_REMINDER = config(
    "BREVO_TEMPLATE_EXPIRY_REMINDER",
    cast=int,
)

BREVO_TEMPLATE_EXPIRED = config(
    "BREVO_TEMPLATE_EXPIRED",
    cast=int,
)

BREVO_TEMPLATE_RENEWED = config(
    "BREVO_TEMPLATE_RENEWED",
    cast=int,
)

BREVO_TEMPLATE_ACTIVATED = config(
    "BREVO_TEMPLATE_ACTIVATED",
    cast=int,
)

BREVO_TEMPLATE_CANCELLED = config(
    "BREVO_TEMPLATE_CANCELLED",
    cast=int,
)
