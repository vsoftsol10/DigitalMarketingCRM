from .base import BasePublisher
from .exceptions import (
    ProviderPublishingError,
    PublishingValidationError,
)


class MetaPublisher(BasePublisher):
    """
    Meta publishing provider.

    Handles Facebook Page and Instagram Professional
    publishing through the Meta Graph API.
    """

    def publish(self, *, post_platform):
        social_account = post_platform.social_account

        if not social_account:
            raise PublishingValidationError(
                "Social account is required for publishing."
            )

        if social_account.platform not in {
            "facebook",
            "instagram",
        }:
            raise PublishingValidationError(
                "Meta publisher supports Facebook and Instagram accounts only."
            )

        if social_account.platform == "facebook":
            return self.publish_facebook(
                post_platform=post_platform,
            )

        if social_account.platform == "instagram":
            return self.publish_instagram(
                post_platform=post_platform,
            )

        raise ProviderPublishingError(
            "Unsupported Meta publishing platform."
        )

    def publish_facebook(self, *, post_platform):
        """
        Publish content to a Facebook Page.

        Actual Meta Graph API implementation will be added
        after the provider contract is verified.
        """
        raise NotImplementedError(
            "Facebook publishing is not implemented yet."
        )

    def publish_instagram(self, *, post_platform):
        """
        Publish content to an Instagram Professional account.

        Actual container creation and publishing flow will be
        added after the provider contract is verified.
        """
        raise NotImplementedError(
            "Instagram publishing is not implemented yet."
        )