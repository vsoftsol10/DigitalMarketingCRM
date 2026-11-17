from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT = config(
    "INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT",
    default=10,
    cast=int,
)
if INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT < 1:
    raise ImproperlyConfigured(
        "INSIGHTS_MAX_MEDIA_PAGES_PER_ATTEMPT must be a positive integer."
    )

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
    "apps.activities",
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
    "apps.dashboard",
    # "apps.integrations.meta",
    "apps.integrations.meta.apps.MetaIntegrationConfig",
    "apps.integrations.instagram.apps.InstagramIntegrationConfig",
]

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
}

# Direct post-media uploads are signed by the API and sent from the browser
# straight to Cloudinary. Keep these limits configurable per deployment/plan;
# they are policy ceilings, not a promise that every destination accepts every
# asset.
MEDIA_UPLOAD_MAX_IMAGE_BYTES = config(
    "MEDIA_UPLOAD_MAX_IMAGE_BYTES",
    default=10_000_000,
    cast=int,
)
MEDIA_UPLOAD_MAX_VIDEO_BYTES = config(
    "MEDIA_UPLOAD_MAX_VIDEO_BYTES",
    default=100_000_000,
    cast=int,
)
MEDIA_UPLOAD_SESSION_TTL_SECONDS = config(
    "MEDIA_UPLOAD_SESSION_TTL_SECONDS",
    default=6 * 60 * 60,
    cast=int,
)
MEDIA_UPLOAD_CHUNK_SIZE_BYTES = config(
    "MEDIA_UPLOAD_CHUNK_SIZE_BYTES",
    default=20 * 1024 * 1024,
    cast=int,
)
MEDIA_UPLOAD_CHUNK_THRESHOLD_BYTES = config(
    "MEDIA_UPLOAD_CHUNK_THRESHOLD_BYTES",
    default=20 * 1024 * 1024,
    cast=int,
)
MEDIA_UPLOAD_ALLOWED_IMAGE_TYPES = tuple(
    item.strip()
    for item in config(
        "MEDIA_UPLOAD_ALLOWED_IMAGE_TYPES",
        default="image/jpeg,image/png,image/webp",
    ).split(",")
    if item.strip()
)
MEDIA_UPLOAD_ALLOWED_VIDEO_TYPES = tuple(
    item.strip()
    for item in config(
        "MEDIA_UPLOAD_ALLOWED_VIDEO_TYPES",
        default="video/mp4,video/quicktime",
    ).split(",")
    if item.strip()
)

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

# Endpoint-specific Redis rate limits. These scopes are configuration only;
# views opt in explicitly by declaring RedisRateThrottle subclasses.
DMC_RATE_LIMITS = {
    "login": ((5, 60), (30, 3600)),
    "token_refresh": ((10, 60), (30, 3600)),
    "media_upload_create": ((20, 60),),
    "media_upload_finalize": ((30, 60),),
    "media_upload_finalize_session": ((5, 60),),
    "ai_caption_generate": ((5, 60), (50, 86400)),
    "publish_now": ((5, 60),),
    "publish_target_now": ((5, 60),),
    "publish_retry": ((3, 60), (20, 3600)),
}
DMC_RATE_LIMIT_REDIS_FAILURE_POLICY = config(
    "DMC_RATE_LIMIT_REDIS_FAILURE_POLICY",
    default="closed",
).strip().lower()
if DMC_RATE_LIMIT_REDIS_FAILURE_POLICY not in {"closed", "open"}:
    raise ImproperlyConfigured(
        "DMC_RATE_LIMIT_REDIS_FAILURE_POLICY must be 'closed' or 'open'."
    )

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:5173",
# ]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://digitalmarketing.thevsoft.com",
]

CORS_ALLOW_HEADERS = [
    *default_headers,
    "idempotency-key",
]
CORS_EXPOSE_HEADERS = ["Retry-After"]

CSRF_TRUSTED_ORIGINS = [
    "https://digitalmarketingcrm.onrender.com",
    "https://digitalmarketing.thevsoft.com",
]

SPECTACULAR_SETTINGS = {
    "TITLE": "Digital Marketing Platform API",
    "DESCRIPTION": "Production API",
    "VERSION": "1.0.0",
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

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

# Minimum spacing between outbound Instagram Graph API requests across workers.
INSTAGRAM_GRAPH_REQUEST_INTERVAL_SECONDS = config(
    "INSTAGRAM_GRAPH_REQUEST_INTERVAL_SECONDS",
    default=1.0,
    cast=float,
)

# ============================================================
# CELERY BEAT
# ============================================================

CELERY_BEAT_SCHEDULE = {
    "daily-insights-dispatcher": {
        "task": "apps.insights.tasks.daily_insights_dispatcher_task",
        "schedule": crontab(hour=8, minute=0),
    },
    "reconcile-insights-sync-work": {
        "task": "apps.insights.tasks.reconcile_insights_sync_work_task",
        "schedule": 60.0,
    },
    "dispatch-due-posts": {
        "task": "apps.posts.tasks.dispatch_due_posts_task",
        "schedule": 60.0,
    },
    "cleanup-expired-media-upload-sessions": {
        "task": "apps.posts.tasks.cleanup_expired_media_upload_sessions_task",
        "schedule": 15 * 60.0,
    },
    "reconcile-ambiguous-instagram-publishes": {
        "task": "apps.posts.tasks.reconcile_ambiguous_instagram_publishes_task",
        "schedule": 300.0,
    },
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
    "maintain-instagram-tokens": {
        "task": ("apps.integrations.instagram.tasks." "maintain_instagram_tokens_task"),
        "schedule": 3600.0,
    },
    "maintain-meta-tokens": {
        "task": ("apps.integrations.meta.tasks." "maintain_meta_tokens_task"),
        "schedule": 3600.0,
    },
    "monitor-meta-user-data-access-expiry": {
        "task": (
            "apps.integrations.meta.tasks."
            "monitor_meta_user_data_access_expiry_task"
        ),
        "schedule": 6 * 60 * 60.0,
    },
    "cleanup-invitation-oauth-secrets": {
        "task": "apps.social_accounts.tasks.cleanup_invitation_oauth_secrets_task",
        "schedule": 60.0,
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

META_USER_TOKEN_AUTO_RENEWAL_ENABLED = config(
    "META_USER_TOKEN_AUTO_RENEWAL_ENABLED",
    default=False,
    cast=bool,
)

META_USER_TOKEN_RENEWAL_WINDOW_SECONDS = config(
    "META_USER_TOKEN_RENEWAL_WINDOW_SECONDS",
    default=7 * 24 * 60 * 60,
    cast=int,
)
if META_USER_TOKEN_RENEWAL_WINDOW_SECONDS < 1:
    raise ImproperlyConfigured(
        "META_USER_TOKEN_RENEWAL_WINDOW_SECONDS must be positive."
    )

META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS = config(
    "META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS",
    default=24 * 60 * 60,
    cast=int,
)
if META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS < 1:
    raise ImproperlyConfigured(
        "META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS must be positive."
    )

META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS = tuple(
    permission.strip()
    for permission in config(
        "META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS",
        default=(
            "read_insights,pages_show_list,business_management,"
            "pages_read_engagement,pages_read_user_content,pages_manage_posts,"
            "public_profile"
        ),
    ).split(",")
    if permission.strip()
)
if not META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS:
    raise ImproperlyConfigured(
        "META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS must not be empty."
    )

META_OAUTH_REDIRECT_URI = config(
    "META_OAUTH_REDIRECT_URI",
    default="",
)

# Invitation OAuth uses a separate callback route so anonymous acceptance
# cannot enter the authenticated direct Facebook callback.
META_INVITATION_OAUTH_REDIRECT_URI = config(
    "META_INVITATION_OAUTH_REDIRECT_URI",
    default="",
)

# Facebook Login for Business configuration.
#
# Login variation, access token type, permissions, and asset selection are
# controlled by the configuration in Meta Developer Dashboard. Django passes
# its ID to Meta through META_BUSINESS_LOGIN_CONFIG_ID. Keep that setting
# aligned with the intended Dashboard configuration.
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

# ============================================================
# META TOKEN LIFECYCLE
# ============================================================

META_TOKEN_LIFECYCLE_LOCK_TIMEOUT_SECONDS = config(
    "META_TOKEN_LIFECYCLE_LOCK_TIMEOUT_SECONDS",
    default=5 * 60,
    cast=int,
)

FRONTEND_URL = config(
    "FRONTEND_URL",
    default="http://localhost:5173",
)

# ============================================================
# INSTAGRAM
# ============================================================

INSTAGRAM_APP_ID = config(
    "INSTAGRAM_APP_ID",
)

INSTAGRAM_APP_SECRET = config(
    "INSTAGRAM_APP_SECRET",
)

INSTAGRAM_GRAPH_API_VERSION = config(
    "INSTAGRAM_GRAPH_API_VERSION",
    default="v26.0",
)

INSTAGRAM_OAUTH_REDIRECT_URI = config(
    "INSTAGRAM_OAUTH_REDIRECT_URI",
    default="",
)

# Separate callback for anonymous invitation authorization. The direct OAuth
# callback remains configured by INSTAGRAM_OAUTH_REDIRECT_URI.
INSTAGRAM_INVITATION_OAUTH_REDIRECT_URI = config(
    "INSTAGRAM_INVITATION_OAUTH_REDIRECT_URI",
    default="",
)

INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS = config(
    "INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS",
    default=600,
    cast=int,
)

INSTAGRAM_HTTP_TIMEOUT_SECONDS = config(
    "INSTAGRAM_HTTP_TIMEOUT_SECONDS",
    default=30,
    cast=int,
)

INSTAGRAM_TOKEN_REFRESH_WINDOW_SECONDS = config(
    "INSTAGRAM_TOKEN_REFRESH_WINDOW_SECONDS",
    default=7 * 24 * 60 * 60,
    cast=int,
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

BREVO_TEMPLATE_SOCIAL_ACCOUNT_INVITATION = config(
    "BREVO_TEMPLATE_SOCIAL_ACCOUNT_INVITATION",
    default=0,
    cast=int,
)


# Low-level HTTP debug output can include credential-bearing request details.
# Filter these loggers before records propagate to Celery or application handlers.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "credential_redaction": {
            "()": "config.log_filters.CredentialRedactionFilter",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "meta_diagnostics_console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "filters": ["require_debug_true", "credential_redaction"],
        },
        "meta_maintenance_console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "filters": ["credential_redaction"],
        },
        "report_error_console": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "filters": ["credential_redaction"],
        },
    },
    "loggers": {
        "apps.integrations.meta.services": {
            "handlers": ["meta_diagnostics_console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.integrations.meta.tasks": {
            "handlers": ["meta_maintenance_console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.integrations.meta.lifecycle": {
            "handlers": ["meta_maintenance_console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.reports.rendering": {
            "handlers": ["report_error_console"],
            "level": "ERROR",
            "propagate": False,
        },
        "urllib3.connectionpool": {
            "filters": ["credential_redaction"],
        },
        "urllib3.connection": {
            "filters": ["credential_redaction"],
        },
        "requests.packages.urllib3.connectionpool": {
            "filters": ["credential_redaction"],
        },
        "http.client": {
            "filters": ["credential_redaction"],
        },
    },
}
