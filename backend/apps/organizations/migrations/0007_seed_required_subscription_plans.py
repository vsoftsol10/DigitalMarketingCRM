from django.db import migrations


REQUIRED_PLANS = {
    "basic": {
        "name": "Basic",
        "code": "basic",
        "plan_type": "BASIC",
        "description": (
            "Perfect for startups and small businesses "
            "looking to build their online presence."
        ),
        "status": "active",
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
    "advanced": {
        "name": "Advanced",
        "code": "advanced",
        "plan_type": "ADVANCED",
        "description": (
            "For large teams with advanced workflows "
            "and higher content demands."
        ),
        "status": "active",
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
}


LEGACY_CUSTOM_PLAN = {
    "name": "Legacy Custom",
    "code": "legacy-custom",
    "plan_type": "CUSTOM",
    "description": (
        "Compatibility plan for subscriptions created before "
        "custom subscriptions referenced the plan catalog."
    ),
    "status": "inactive",
    "monthly_price": 0,
    "yearly_price": 0,
    "accounts_limit": 0,
    "posts_limit": 0,
    "videos_limit": 0,
    "ads_limit": 0,
    "dm_automations_limit": 0,
    "highlights": "",
    "is_system": True,
    "is_custom": True,
}


def seed_required_subscription_plans(apps, schema_editor):
    OrganizationSubscription = apps.get_model(
        "organizations",
        "OrganizationSubscription",
    )
    Plan = apps.get_model("plans", "Plan")
    database = schema_editor.connection.alias

    plans_to_ensure = list(REQUIRED_PLANS.values())
    has_custom_subscriptions = OrganizationSubscription.objects.using(
        database,
    ).filter(
        plan="CUSTOM",
    ).exists()
    if has_custom_subscriptions:
        plans_to_ensure.append(LEGACY_CUSTOM_PLAN)

    for plan_data in plans_to_ensure:
        plan_manager = Plan.objects.using(database)
        if plan_manager.filter(code=plan_data["code"]).exists():
            continue

        name_conflict = plan_manager.filter(name=plan_data["name"]).exists()
        if name_conflict:
            raise RuntimeError(
                "Cannot create required subscription Plan with code "
                f"{plan_data['code']!r}: a Plan with name "
                f"{plan_data['name']!r} already exists under another code. "
                "Resolve the Plan identity conflict before migrating."
            )

        plan_manager.create(**plan_data)


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0007_organizationsubscription_plan_reference"),
        ("plans", "0004_remove_plan_billing_cycle"),
    ]

    operations = [
        migrations.RunPython(
            seed_required_subscription_plans,
            migrations.RunPython.noop,
        ),
    ]
