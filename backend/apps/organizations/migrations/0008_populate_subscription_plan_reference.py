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


def populate_subscription_plan_reference(
    apps,
    schema_editor,
):
    OrganizationSubscription = apps.get_model(
        "organizations",
        "OrganizationSubscription",
    )

    Plan = apps.get_model(
        "plans",
        "Plan",
    )

    database = schema_editor.connection.alias

    # Check every needed target before changing any subscription rows.
    has_custom_subscriptions = OrganizationSubscription.objects.using(
        database,
    ).filter(
        plan="CUSTOM",
    ).exists()

    required_plan_codes = {"basic", "advanced"}
    if has_custom_subscriptions:
        required_plan_codes.add("legacy-custom")

    plans_to_ensure = list(REQUIRED_PLANS.values())
    if has_custom_subscriptions:
        plans_to_ensure.append(LEGACY_CUSTOM_PLAN)

    for plan_data in plans_to_ensure:
        plan_manager = Plan.objects.using(database)
        if plan_manager.filter(code=plan_data["code"]).exists():
            continue

        if plan_manager.filter(name=plan_data["name"]).exists():
            raise RuntimeError(
                "Cannot create required subscription Plan with code "
                f"{plan_data['code']!r}: a Plan with name "
                f"{plan_data['name']!r} already exists under another code. "
                "Resolve the Plan identity conflict before migrating."
            )

        plan_manager.create(**plan_data)

    plans_by_code = dict(
        Plan.objects.using(database).filter(
            code__in=required_plan_codes,
        ).values_list(
            "code",
            "pk",
        )
    )

    missing_plan_codes = sorted(required_plan_codes - plans_by_code.keys())
    if missing_plan_codes:
        missing = ", ".join(missing_plan_codes)
        raise RuntimeError(
            "Cannot migrate organization subscription plan references: "
            f"required Plan record(s) are missing for code(s): {missing}. "
            "Create the approved Plan record(s), then rerun this migration."
        )

    # BASIC -> Basic. Keep any reference already assigned.
    OrganizationSubscription.objects.using(database).filter(
        plan="BASIC",
        plan_reference__isnull=True,
    ).update(
        plan_reference_id=plans_by_code["basic"],
    )

    # ADVANCE -> Advanced
    OrganizationSubscription.objects.using(database).filter(
        plan="ADVANCE",
        plan_reference__isnull=True,
    ).update(
        plan_reference_id=plans_by_code["advanced"],
    )

    # CUSTOM -> Legacy Custom Plan
    if has_custom_subscriptions:
        OrganizationSubscription.objects.using(database).filter(
            plan="CUSTOM",
            plan_reference__isnull=True,
        ).update(
            plan_reference_id=plans_by_code["legacy-custom"],
        )

    unmapped_subscriptions = OrganizationSubscription.objects.using(
        database,
    ).filter(
        plan_reference__isnull=True,
    )
    unmapped_count = unmapped_subscriptions.count()
    if unmapped_count:
        raise RuntimeError(
            "Cannot migrate organization subscription plan references: "
            f"{unmapped_count} subscription record(s) remain without a Plan "
            "reference after mapping BASIC, ADVANCE, and CUSTOM. Check for "
            "unrecognized legacy plan values and add an explicit mapping "
            "before rerunning this migration."
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0007_organizationsubscription_plan_reference",
        ),
        (
            "plans",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.RunPython(
            populate_subscription_plan_reference,
            migrations.RunPython.noop,
        ),
    ]
