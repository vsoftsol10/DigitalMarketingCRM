#reconect change
# 
# import uuid

# from django.core import signing

# from .constants import (
#     INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS,
# )
# from .exceptions import InstagramOAuthStateError


# STATE_SALT = "instagram-oauth-state"


# def create_oauth_state(
#     *,
#     organization_id,
#     user_id,
#     nonce,
# ):
#     payload = {
#         "organization_id": str(
#             organization_id
#         ),
#         "user_id": str(
#             user_id
#         ),
#         "nonce": str(nonce),
#     }

#     return signing.dumps(
#         payload,
#         salt=STATE_SALT,
#     )


# def create_oauth_nonce():
#     return uuid.uuid4()


# def validate_oauth_state(
#     state,
# ):
#     if not state:
#         raise InstagramOAuthStateError(
#             "Instagram OAuth state is missing."
#         )

#     try:
#         return signing.loads(
#             state,
#             salt=STATE_SALT,
#             max_age=INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS,
#         )
#     except signing.BadSignature as exc:
#         raise InstagramOAuthStateError(
#             "Instagram OAuth state is invalid or expired."
#         ) from exc

import uuid

from django.core import signing

from .constants import (
    INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS,
)
from .exceptions import InstagramOAuthStateError

STATE_SALT = "instagram-oauth-state"


# ============================================================
# OAUTH ACTIONS
# ============================================================

OAUTH_ACTION_CONNECT = "connect"
OAUTH_ACTION_RECONNECT = "reconnect"

ALLOWED_OAUTH_ACTIONS = {
    OAUTH_ACTION_CONNECT,
    OAUTH_ACTION_RECONNECT,
}


# ============================================================
# CREATE OAUTH STATE
# ============================================================


def create_oauth_state(
    *,
    organization_id,
    user_id,
    nonce,
    action=OAUTH_ACTION_CONNECT,
    social_account_id=None,
):
    action = str(action or "").strip().lower()

    if action not in ALLOWED_OAUTH_ACTIONS:
        raise InstagramOAuthStateError("Invalid Instagram OAuth action.")

    payload = {
        "organization_id": str(organization_id),
        "user_id": str(user_id),
        "nonce": str(nonce),
        "action": action,
    }

    # --------------------------------------------------------
    # Reconnect must always contain the target SocialAccount.
    # --------------------------------------------------------

    if action == OAUTH_ACTION_RECONNECT:
        if not social_account_id:
            raise InstagramOAuthStateError(
                "Social account ID is required for reconnect."
            )

        payload["social_account_id"] = str(social_account_id)

    return signing.dumps(
        payload,
        salt=STATE_SALT,
    )


# ============================================================
# CREATE OAUTH NONCE
# ============================================================


def create_oauth_nonce():
    return uuid.uuid4()


# ============================================================
# VALIDATE OAUTH STATE
# ============================================================


def validate_oauth_state(
    state,
):
    if not state:
        raise InstagramOAuthStateError("Instagram OAuth state is missing.")

    try:
        payload = signing.loads(
            state,
            salt=STATE_SALT,
            max_age=INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS,
        )

    except signing.BadSignature as exc:
        raise InstagramOAuthStateError(
            "Instagram OAuth state is invalid or expired."
        ) from exc

    # --------------------------------------------------------
    # Validate payload structure
    # --------------------------------------------------------

    if not isinstance(payload, dict):
        raise InstagramOAuthStateError("Instagram OAuth state payload is invalid.")

    organization_id = payload.get("organization_id")

    if not organization_id:
        raise InstagramOAuthStateError(
            "Instagram OAuth state does not contain " "organization information."
        )

    user_id = payload.get("user_id")

    if not user_id:
        raise InstagramOAuthStateError(
            "Instagram OAuth state does not contain " "user information."
        )

    # --------------------------------------------------------
    # Backward compatibility
    #
    # Existing connect states may not contain "action".
    # Treat those states as normal CONNECT.
    # --------------------------------------------------------

    action = str(payload.get("action") or OAUTH_ACTION_CONNECT).strip().lower()

    if action not in ALLOWED_OAUTH_ACTIONS:
        raise InstagramOAuthStateError(
            "Instagram OAuth state contains an invalid action."
        )

    payload["action"] = action

    # --------------------------------------------------------
    # Reconnect state validation
    # --------------------------------------------------------

    if action == OAUTH_ACTION_RECONNECT:
        social_account_id = payload.get("social_account_id")

        if not social_account_id:
            raise InstagramOAuthStateError(
                "Instagram OAuth state does not contain "
                "the reconnect SocialAccount information."
            )

    return payload
