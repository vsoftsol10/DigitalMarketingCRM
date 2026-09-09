from apps.social.models import SocialConnectionProvider

from .exceptions import UnsupportedPublishingPlatformError
from .meta import MetaPublisher


PUBLISHER_REGISTRY = {
    SocialConnectionProvider.META: MetaPublisher,
}


def get_publisher(*, provider):
    publisher_class = PUBLISHER_REGISTRY.get(provider)

    if not publisher_class:
        raise UnsupportedPublishingPlatformError(
            f"No publisher configured for provider '{provider}'."
        )

    return publisher_class()