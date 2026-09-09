from django.conf import settings

# ============================================================
# META GRAPH API
# ============================================================

META_GRAPH_BASE_URL = (
    f"https://graph.facebook.com/" f"{settings.META_GRAPH_API_VERSION}"
)


# ============================================================
# FACEBOOK LOGIN FOR BUSINESS
# ============================================================

META_OAUTH_AUTHORIZE_URL = (
    f"https://www.facebook.com/" f"{settings.META_GRAPH_API_VERSION}/dialog/oauth"
)

META_TOKEN_URL = f"{META_GRAPH_BASE_URL}/oauth/access_token"


# ============================================================
# OAUTH SECURITY
# ============================================================

META_OAUTH_STATE_MAX_AGE_SECONDS = 600


# ============================================================
# META API
# ============================================================

META_HTTP_TIMEOUT_SECONDS = getattr(
    settings,
    "META_HTTP_TIMEOUT_SECONDS",
    30,
)


# ============================================================
# META PAGE DISCOVERY
# ============================================================

# Meta's Facebook Login / Instagram API flow uses the
# Facebook Page as the parent asset and exposes the linked
# Instagram Professional account through
# instagram_business_account.
#
# We intentionally do not request `tasks` because the current
# project Graph API tests showed that field can be rejected
# for the configured token/configuration.

META_PAGE_FIELDS = "id," "name," "access_token," "instagram_business_account"

META_PAGE_DETAIL_FIELDS = "id," "name," "access_token," "instagram_business_account"


# ============================================================
# INSTAGRAM PROFILE
# ============================================================

META_INSTAGRAM_PROFILE_FIELDS = "id," "username," "name," "profile_picture_url"
