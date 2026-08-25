from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0011_make_subscription_dates_required",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE organization_subscriptions
                DROP CONSTRAINT IF EXISTS
                organization_subscriptions_organization_id_key;
            """,
            reverse_sql="""
                ALTER TABLE organization_subscriptions
                ADD CONSTRAINT
                organization_subscriptions_organization_id_key
                UNIQUE (organization_id);
            """,
        ),
    ]