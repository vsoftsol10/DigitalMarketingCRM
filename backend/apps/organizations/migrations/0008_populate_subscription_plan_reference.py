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

    # BASIC -> Basic
    basic_plan = Plan.objects.get(
        code="basic",
    )

    OrganizationSubscription.objects.filter(
        plan="BASIC",
    ).update(
        plan_reference_id=basic_plan.id,
    )

    # ADVANCE -> Advanced
    advanced_plan = Plan.objects.get(
        code="advanced",
    )

    OrganizationSubscription.objects.filter(
        plan="ADVANCE",
    ).update(
        plan_reference_id=advanced_plan.id,
    )

    # CUSTOM -> Legacy Custom Plan
    legacy_custom_plan = Plan.objects.get(
        code="legacy-custom",
    )

    OrganizationSubscription.objects.filter(
        plan="CUSTOM",
    ).update(
        plan_reference_id=legacy_custom_plan.id,
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