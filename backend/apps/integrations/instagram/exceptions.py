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
        usage_diagnostics=None,
    ):
        super().__init__(message)

        self.status_code = status_code
        self.error_payload = error_payload or {}
        # This is an ephemeral, allowlisted subset of Meta response-header
        # usage data. It never contains request headers or credentials.
        self.usage_diagnostics = usage_diagnostics or {}
