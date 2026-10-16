from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0007_organizationsubscription_plan_reference"),
        ("plans", "0004_remove_plan_billing_cycle"),
    ]

    # Kept as a no-op so environments that recorded this migration retain a
    # valid migration identity. Required plans are ensured by migration 0008,
    # which remains compatible with databases where it was already applied.
    operations = []
