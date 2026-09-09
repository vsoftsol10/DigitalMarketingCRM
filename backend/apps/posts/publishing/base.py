from abc import ABC, abstractmethod


class BasePublisher(ABC):
    """
    Base interface for social-media publishers.

    Each provider/platform implementation must expose
    the same publishing contract to the posts service.
    """

    @abstractmethod
    def publish(self, *, post_platform):
        """
        Publish one PostPlatform target.

        Returns:
            dict containing provider response information.
        """
        raise NotImplementedError