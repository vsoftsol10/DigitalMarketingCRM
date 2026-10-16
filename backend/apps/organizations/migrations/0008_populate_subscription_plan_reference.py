from django.db import migrations


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
            "0007_seed_required_subscription_plans",
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
