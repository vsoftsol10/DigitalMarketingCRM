from django.core import signing

from .exceptions import MetaOAuthStateError

STATE_SALT = "meta-oauth-state"


def create_oauth_state(
    *,
    organization_id,
    user_id,
):
    """
    Create a signed OAuth state binding the flow to:

        authenticated user
        selected organization

    The signed value is self-contained and time-bound by the
    max_age supplied during validation.
    """

    payload = {
        "organization_id": str(
            organization_id,
        ),
        "user_id": str(
            user_id,
        ),
    }

    return signing.dumps(
        payload,
        salt=STATE_SALT,
    )


def validate_oauth_state(
    state,
    *,
    max_age,
):
    """
    Validate and decode a signed OAuth state.
    """

    if not state:
        raise MetaOAuthStateError(
            "OAuth state is required.",
        )

    try:
        payload = signing.loads(
            state,
            salt=STATE_SALT,
            max_age=max_age,
        )

    except (
        signing.BadSignature,
        signing.SignatureExpired,
    ) as exc:
        raise MetaOAuthStateError(
            "Invalid or expired OAuth state.",
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise MetaOAuthStateError(
            "Invalid OAuth state payload.",
        )

    organization_id = payload.get(
        "organization_id",
    )

    user_id = payload.get(
        "user_id",
    )

    if not organization_id:
        raise MetaOAuthStateError(
            "OAuth state does not contain organization information.",
        )

    if not user_id:
        raise MetaOAuthStateError(
            "OAuth state does not contain user information.",
        )

    return payload
