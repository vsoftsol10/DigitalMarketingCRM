from django.core.management.base import BaseCommand

from apps.plans.models import (
    BillingCycle,
    Plan,
    PlanStatus,
)

DEFAULT_PLANS = [
    {
        "name": "Basic",
        "code": "basic",
        "plan_type": "BASIC",
        "description": (
            "Perfect for startups and small businesses "
            "looking to build their online presence."
        ),
        "status": PlanStatus.ACTIVE,
        "billing_cycle": BillingCycle.MONTHLY,
        "monthly_price": 9999,
        "yearly_price": 99999,
        "accounts_limit": 3,
        "posts_limit": 50,
        "videos_limit": 20,
        "ads_limit": 5,
        "dm_automations_limit": 10,
        "highlights": "",
        "is_system": True,
        "is_custom": False,
    },
    {
        "name": "Premium",
        "code": "premium",
        "plan_type": "PREMIUM",
        "description": (
            "For established agencies managing multiple "
            "clients with high content volume."
        ),
        "status": PlanStatus.ACTIVE,
        "billing_cycle": BillingCycle.MONTHLY,
        "monthly_price": 29999,
        "yearly_price": 299999,
        "accounts_limit": 15,
        "posts_limit": 300,
        "videos_limit": 120,
        "ads_limit": 30,
        "dm_automations_limit": 50,
        "highlights": "",
        "is_system": True,
        "is_custom": False,
    },
    {
        "name": "Advanced",
        "code": "advanced",
        "plan_type": "ADVANCED",
        "description": (
            "For large teams with advanced workflows " "and higher content demands."
        ),
        "status": PlanStatus.ACTIVE,
        "billing_cycle": BillingCycle.MONTHLY,
        "monthly_price": 49999,
        "yearly_price": 499999,
        "accounts_limit": 30,
        "posts_limit": 800,
        "videos_limit": 250,
        "ads_limit": 60,
        "dm_automations_limit": 100,
        "highlights": "",
        "is_system": True,
        "is_custom": False,
    },
]


class Command(BaseCommand):
    help = "Seed default system subscription plans."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for plan_data in DEFAULT_PLANS:
            code = plan_data["code"]

            plan = Plan.objects.filter(code=code).first()

            if plan:
                protected_fields = {
                    key: value
                    for key, value in plan_data.items()
                    if key
                    not in {
                        "code",
                        "plan_type",
                        "is_system",
                        "is_custom",
                    }
                }

                for field, value in protected_fields.items():
                    setattr(
                        plan,
                        field,
                        value,
                    )

                plan.is_system = True
                plan.is_custom = False

                plan.save()

                updated_count += 1

            else:
                Plan.objects.create(**plan_data)

                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Default plans seeded successfully. "
                f"Created: {created_count}, "
                f"Updated: {updated_count}"
            )
        )
