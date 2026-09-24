class PublishingError(Exception):
    """Base exception for publishing failures."""


class UnsupportedPublishingPlatformError(PublishingError):
    """Raised when no publisher exists for a platform."""


class PublishingValidationError(PublishingError):
    """Raised when post data is invalid for publishing."""


class ProviderPublishingError(PublishingError):
    """Raised when the external provider rejects the publish request."""


class MediaProcessingPending(PublishingError):
    """Raised when a provider container exists but is not ready to publish."""

    def __init__(self, message, *, rate_limited=False):
        super().__init__(message)
        self.rate_limited = rate_limited
