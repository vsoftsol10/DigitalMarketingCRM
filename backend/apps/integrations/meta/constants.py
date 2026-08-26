# ============================================================
# META OAUTH
# ============================================================

META_GRAPH_API_VERSION = "vXX.X"

META_GRAPH_BASE_URL = (
    f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"
)

META_OAUTH_AUTHORIZE_URL = (
    "https://www.facebook.com/"
    f"{META_GRAPH_API_VERSION}/dialog/oauth"
)

META_TOKEN_URL = (
    f"{META_GRAPH_BASE_URL}/oauth/access_token"
)

META_OAUTH_STATE_MAX_AGE_SECONDS = 600