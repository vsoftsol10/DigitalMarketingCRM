import uuid

from django.core import signing

from .constants import (
    INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS,
)
from .exceptions import InstagramOAuthStateError


STATE_SALT = "instagram-oauth-state"


def create_oauth_state(
    *,
    organization_id,
    user_id,
    nonce,
):
    payload = {
        "organization_id": str(
            organization_id
        ),
        "user_id": str(
            user_id
        ),
        "nonce": str(nonce),
    }

    return signing.dumps(
        payload,
        salt=STATE_SALT,
    )


def create_oauth_nonce():
    return uuid.uuid4()


def validate_oauth_state(
    state,
):
    if not state:
        raise InstagramOAuthStateError(
            "Instagram OAuth state is missing."
        )

    try:
        return signing.loads(
            state,
            salt=STATE_SALT,
            max_age=INSTAGRAM_OAUTH_STATE_MAX_AGE_SECONDS,
        )
    except signing.BadSignature as exc:
        raise InstagramOAuthStateError(
            "Instagram OAuth state is invalid or expired."
        ) from exc