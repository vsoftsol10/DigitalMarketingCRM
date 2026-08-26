from dataclasses import dataclass


@dataclass(frozen=True)
class MetaAccountData:
    """
    Normalized social-account data returned by Meta discovery.
    """

    platform: str
    platform_account_id: str
    account_name: str
    username: str
    profile_image: str


class MetaAccountDiscoveryService:
    """
    Responsible for discovering social accounts available
    to the authenticated Meta connection.

    Provider-specific Graph API calls will be implemented
    here once the required Meta permissions are confirmed.
    """

    def __init__(self, *, access_token):
        self.access_token = access_token

    def discover_accounts(self):
        """
        Discover Facebook and Instagram accounts.

        This method will later:
        1. Fetch Facebook Pages.
        2. Identify connected Instagram accounts.
        3. Normalize provider data.
        4. Return MetaAccountData objects.
        """

        raise NotImplementedError(
            "Meta account discovery requires the "
            "confirmed Meta permissions and API version."
        )
        
from django.db import transaction

from apps.social_accounts.services import create_social_account

from .exceptions import MetaIntegrationError


class MetaSocialAccountService:
    """
    Convert discovered Meta account data into the generic
    SocialAccount model.
    """

    @transaction.atomic
    def connect_account(
        self,
        *,
        organization,
        account_data,
        access_token,
        refresh_token="",
        token_expires_at=None,
    ):
        if not account_data:
            raise MetaIntegrationError(
                "No Meta social account data was provided."
            )

        required_fields = (
            "platform",
            "platform_account_id",
        )

        for field in required_fields:
            if not account_data.get(field):
                raise MetaIntegrationError(
                    f"Meta account data is missing '{field}'."
                )

        validated_data = {
            "platform": account_data["platform"],
            "platform_account_id": account_data[
                "platform_account_id"
            ],
            "account_name": account_data.get(
                "account_name",
                "",
            ),
            "username": account_data.get(
                "username",
                "",
            ),
            "profile_image": account_data.get(
                "profile_image",
                "",
            ),
        }

        social_account = create_social_account(
            organization=organization,
            validated_data=validated_data,
        )

        # OAuth credentials are controlled by the
        # integration layer, never by the frontend.

        social_account.access_token = access_token
        social_account.refresh_token = refresh_token
        social_account.token_expires_at = token_expires_at

        social_account.save(
            update_fields=[
                "access_token",
                "refresh_token",
                "token_expires_at",
                "updated_at",
            ]
        )

        return social_account