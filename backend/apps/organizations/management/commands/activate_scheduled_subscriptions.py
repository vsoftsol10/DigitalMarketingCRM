from django.core.management.base import BaseCommand

from apps.organizations.services import (
    activate_due_scheduled_subscriptions,
)


class Command(BaseCommand):
    help = (
        "Activate scheduled organization subscriptions " "whose start date has arrived."
    )

    def handle(self, *args, **options):
        activated_count = activate_due_scheduled_subscriptions()

        self.stdout.write(
            self.style.SUCCESS(
                f"Activated {activated_count} " f"scheduled subscription(s)."
            )
        )
