from django.conf import settings


INSTAGRAM_OAUTH_AUTHORIZE_URL = (
    "https://www.instagram.com/oauth/authorize"
)

INSTAGRAM_TOKEN_URL = (
    "https://api.instagram.com/oauth/access_token"
)

INSTAGRAM_GRAPH_BASE_URL = (
    "https://graph.instagram.com"
)

INSTAGRAM_GRAPH_API_VERSION = getattr(
    settings,
    "INSTAGRAM_GRAPH_API_VERSION",
    "v26.0",
)

INSTAGRAM_OAUTH_REDIRECT_URI = getattr(
    settings,
    "INSTAGRAM_OAUTH_REDIRECT_URI",
    "",
)

INSTAGRAM_OAUTH_SCOPES = (
    "instagram_business_basic",
    "instagram_business_content_publish",
)

INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS = getattr(
    settings,
    "INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS",
    600,
)

INSTAGRAM_HTTP_TIMEOUT_SECONDS = getattr(
    settings,
    "INSTAGRAM_HTTP_TIMEOUT_SECONDS",
    30,
)

INSTAGRAM_PROFILE_FIELDS = (
    "id,"
    "username,"
    "name,"
    "profile_picture_url"
)

INSTAGRAM_LONG_LIVED_TOKEN_DEFAULT_SECONDS = (
    60 * 24 * 60 * 60
)
