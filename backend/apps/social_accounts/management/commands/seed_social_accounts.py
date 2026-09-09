from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import transaction

from apps.organizations.models import Organization

from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialPlatform,
)


class Command(BaseCommand):
    help = "Seed organization-specific social accounts for development/testing."

    # ============================================================
    # DEVELOPMENT SEED DATA
    # ============================================================
    #
    # These records represent the shape of accounts that will
    # later be created from provider integrations such as Meta.
    #
    # IMPORTANT:
    # - These are test records only.
    # - They are attached to one specific organization.
    # - Provider-specific OAuth credentials are NOT stored here.
    #
    # ============================================================

    SEED_ACCOUNTS = {
        SocialPlatform.INSTAGRAM: [
            {
                "platform_account_id": ("seed-org-instagram-001"),
                "account_name": "Atlas Fitness",
                "username": "@atlasfitness",
                "profile_image": "",
            },
            {
                "platform_account_id": ("seed-org-instagram-002"),
                "account_name": "Atlas Fitness Training",
                "username": "@atlastraining",
                "profile_image": "",
            },
        ],
        SocialPlatform.FACEBOOK: [
            {
                "platform_account_id": ("seed-org-facebook-001"),
                "account_name": "Atlas Fitness",
                "username": "Atlas Fitness",
                "profile_image": "",
            },
        ],
        SocialPlatform.LINKEDIN: [
            {
                "platform_account_id": ("seed-org-linkedin-001"),
                "account_name": "Atlas Fitness",
                "username": "Atlas Fitness",
                "profile_image": "",
            },
        ],
        SocialPlatform.YOUTUBE: [
            {
                "platform_account_id": ("seed-org-youtube-001"),
                "account_name": "Atlas Fitness Channel",
                "username": "@atlasfitnesschannel",
                "profile_image": "",
            },
        ],
    }

    # ============================================================
    # COMMAND ARGUMENTS
    # ============================================================

    def add_arguments(self, parser):
        parser.add_argument(
            "--organization-id",
            dest="organization_id",
            required=True,
            help=(
                "Organization ID for which development "
                "social accounts should be seeded."
            ),
        )

    # ============================================================
    # HANDLE
    # ============================================================

    @transaction.atomic
    def handle(self, *args, **options):
        organization_id = options["organization_id"]

        # ========================================================
        # FIND ORGANIZATION
        # ========================================================

        organization = Organization.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).first()

        if not organization:
            raise CommandError((f"Organization '{organization_id}' " "was not found."))

        self.stdout.write(
            (
                f"Seeding social accounts for "
                f"{organization.organization_id} - "
                f"{organization.name}"
            )
        )

        # ========================================================
        # COUNTERS
        # ========================================================

        created_count = 0
        existing_count = 0

        # ========================================================
        # CREATE / REUSE
        # ========================================================

        for platform, accounts in self.SEED_ACCOUNTS.items():
            for account_data in accounts:
                (
                    social_account,
                    created,
                ) = SocialAccount.objects.get_or_create(
                    organization=organization,
                    platform=platform,
                    platform_account_id=(account_data["platform_account_id"]),
                    is_deleted=False,
                    defaults={
                        "account_name": (account_data["account_name"]),
                        "username": (account_data["username"]),
                        "profile_image": (account_data["profile_image"]),
                        "status": (SocialAccountStatus.CONNECTED),
                        "is_valid": True,
                        "last_synced_at": None,
                    },
                )

                if created:
                    created_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            (
                                "Created: "
                                f"{social_account.platform} "
                                f"- "
                                f"{social_account.username or social_account.account_name}"
                            )
                        )
                    )
                else:
                    existing_count += 1

                    self.stdout.write(
                        self.style.WARNING(
                            (
                                "Already exists: "
                                f"{social_account.platform} "
                                f"- "
                                f"{social_account.username or social_account.account_name}"
                            )
                        )
                    )

        # ========================================================
        # SUMMARY
        # ========================================================

        total_count = sum(len(accounts) for accounts in self.SEED_ACCOUNTS.values())

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Social account seed completed."))

        self.stdout.write(f"Organization: {organization.organization_id}")

        self.stdout.write(f"Created: {created_count}")

        self.stdout.write(f"Already existed: {existing_count}")

        self.stdout.write(f"Expected seed accounts: {total_count}")
