class InstagramIntegrationError(Exception):
    """
    Base exception for Instagram integration failures.
    """


class InstagramOAuthStateError(
    InstagramIntegrationError
):
    """
    Raised when OAuth state validation fails.
    """


class InstagramOAuthConfigurationError(
    InstagramIntegrationError
):
    """
    Raised when Instagram OAuth configuration is invalid.
    """


class InstagramAPIError(
    InstagramIntegrationError
):
    """
    Raised when Instagram API returns an error.
    """

    def __init__(
        self,
        message,
        *,
        status_code=None,
        error_payload=None,
    ):
        super().__init__(message)

        self.status_code = status_code
        self.error_payload = error_payload or {}