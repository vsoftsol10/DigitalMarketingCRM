class MetaIntegrationError(Exception):
    """
    Base exception for Meta integration failures.
    """


class MetaOAuthStateError(MetaIntegrationError):
    """
    Raised when OAuth state is invalid, expired,
    malformed, or cannot be trusted.
    """


class MetaOAuthConfigurationError(MetaIntegrationError):
    """
    Raised when Meta OAuth configuration is incomplete.
    """


class MetaAPIError(MetaIntegrationError):
    """
    Raised when Meta Graph API returns an error
    or an unexpected response.
    """

    def __init__(
        self,
        message,
        *,
        status_code=None,
        error_payload=None,
    ):
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.error_payload = error_payload or {}