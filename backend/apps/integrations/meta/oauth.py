# Reconect change

# from django.core import signing

# from .exceptions import MetaOAuthStateError

# STATE_SALT = "meta-oauth-state"


# def create_oauth_state(
#     *,
#     organization_id,
#     user_id,
# ):
#     """
#     Create a signed OAuth state binding the flow to:

#         authenticated user
#         selected organization

#     The signed value is self-contained and time-bound by the
#     max_age supplied during validation.
#     """

#     payload = {
#         "organization_id": str(
#             organization_id,
#         ),
#         "user_id": str(
#             user_id,
#         ),
#     }

#     return signing.dumps(
#         payload,
#         salt=STATE_SALT,
#     )


# def validate_oauth_state(
#     state,
#     *,
#     max_age,
# ):
#     """
#     Validate and decode a signed OAuth state.
#     """

#     if not state:
#         raise MetaOAuthStateError(
#             "OAuth state is required.",
#         )

#     try:
#         payload = signing.loads(
#             state,
#             salt=STATE_SALT,
#             max_age=max_age,
#         )

#     except (
#         signing.BadSignature,
#         signing.SignatureExpired,
#     ) as exc:
#         raise MetaOAuthStateError(
#             "Invalid or expired OAuth state.",
#         ) from exc

#     if not isinstance(
#         payload,
#         dict,
#     ):
#         raise MetaOAuthStateError(
#             "Invalid OAuth state payload.",
#         )

#     organization_id = payload.get(
#         "organization_id",
#     )

#     user_id = payload.get(
#         "user_id",
#     )

#     if not organization_id:
#         raise MetaOAuthStateError(
#             "OAuth state does not contain organization information.",
#         )

#     if not user_id:
#         raise MetaOAuthStateError(
#             "OAuth state does not contain user information.",
#         )

#     return payload



from django.core import signing

from .exceptions import MetaOAuthStateError

STATE_SALT = "meta-oauth-state"

OAUTH_ACTION_CONNECT = "connect"
OAUTH_ACTION_RECONNECT = "reconnect"

ALLOWED_OAUTH_ACTIONS = {
    OAUTH_ACTION_CONNECT,
    OAUTH_ACTION_RECONNECT,
}


def create_oauth_state(
    *,
    organization_id,
    user_id,
    action=OAUTH_ACTION_CONNECT,
    social_account_id=None,
):
    """
    Create a signed and time-bound OAuth state.

    The state binds the OAuth flow to:

        authenticated user
        selected organization
        OAuth action

    For reconnect flows it additionally binds the flow to
    one specific SocialAccount.

    IMPORTANT:
    The returned state is signed by Django and therefore
    cannot be modified by the frontend without invalidating
    the signature.
    """

    action = str(action or "").strip().lower()

    if action not in ALLOWED_OAUTH_ACTIONS:
        raise MetaOAuthStateError(
            "Invalid OAuth action.",
        )

    payload = {
        "organization_id": str(
            organization_id,
        ),
        "user_id": str(
            user_id,
        ),
        "action": action,
    }

    # --------------------------------------------------------
    # RECONNECT TARGET
    # --------------------------------------------------------

    if action == OAUTH_ACTION_RECONNECT:
        if not social_account_id:
            raise MetaOAuthStateError(
                "Social account ID is required for reconnect.",
            )

        payload["social_account_id"] = str(
            social_account_id,
        )

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

    Validation guarantees:

        - state exists
        - signature is valid
        - state has not expired
        - payload is a dictionary
        - organization_id exists
        - user_id exists
        - action is valid
        - reconnect contains social_account_id

    The returned payload can safely be used by the OAuth
    callback to determine the intended OAuth operation.
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

    # --------------------------------------------------------
    # PAYLOAD
    # --------------------------------------------------------

    if not isinstance(
        payload,
        dict,
    ):
        raise MetaOAuthStateError(
            "Invalid OAuth state payload.",
        )

    # --------------------------------------------------------
    # ORGANIZATION
    # --------------------------------------------------------

    organization_id = payload.get(
        "organization_id",
    )

    if not organization_id:
        raise MetaOAuthStateError(
            "OAuth state does not contain organization information.",
        )

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    user_id = payload.get(
        "user_id",
    )

    if not user_id:
        raise MetaOAuthStateError(
            "OAuth state does not contain user information.",
        )

    # --------------------------------------------------------
    # ACTION
    # --------------------------------------------------------

    action = (
        str(
            payload.get("action") or "",
        )
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # BACKWARD COMPATIBILITY
    #
    # Existing normal CONNECT states created before this
    # change do not contain "action".
    #
    # Treat those states as CONNECT.
    # --------------------------------------------------------

    if not action:
        action = OAUTH_ACTION_CONNECT
        payload["action"] = action

    if action not in ALLOWED_OAUTH_ACTIONS:
        raise MetaOAuthStateError(
            "OAuth state contains an invalid action.",
        )

    # --------------------------------------------------------
    # RECONNECT TARGET
    # --------------------------------------------------------

    if action == OAUTH_ACTION_RECONNECT:
        social_account_id = payload.get(
            "social_account_id",
        )

        if not social_account_id:
            raise MetaOAuthStateError(
                "OAuth state does not contain the reconnect "
                "SocialAccount information.",
            )

    return payload
