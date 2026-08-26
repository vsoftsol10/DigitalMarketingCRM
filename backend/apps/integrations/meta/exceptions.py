class MetaIntegrationError(Exception):
    """Base exception for Meta integration errors."""


class MetaOAuthStateError(MetaIntegrationError):
    """Raised when OAuth state is invalid or expired."""


class MetaOAuthConfigurationError(MetaIntegrationError):
    """Raised when Meta OAuth configuration is incomplete."""