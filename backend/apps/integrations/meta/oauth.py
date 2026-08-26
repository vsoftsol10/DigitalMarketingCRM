from django.core import signing


STATE_SALT = "meta-oauth-state"


def create_oauth_state(*, organization_id, user_id):
    """
    Create a signed and time-bound OAuth state.

    The state binds the OAuth flow to:
    - authenticated user
    - selected organization
    """

    payload = {
        "organization_id": organization_id,
        "user_id": str(user_id),
    }

    return signing.dumps(
        payload,
        salt=STATE_SALT,
    )


def validate_oauth_state(state, *, max_age):
    """
    Validate and decode a Meta OAuth state.

    Raises signing exceptions when the state is:
    - invalid
    - tampered with
    - expired
    """

    return signing.loads(
        state,
        salt=STATE_SALT,
        max_age=max_age,
    )