from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "organizations",
            "0010_finalize_subscription_model",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE organization_subscriptions
                ALTER COLUMN start_date SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE organization_subscriptions
                ALTER COLUMN start_date DROP NOT NULL;
            """,
        ),

        migrations.RunSQL(
            sql="""
                ALTER TABLE organization_subscriptions
                ALTER COLUMN expiry_date SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE organization_subscriptions
                ALTER COLUMN expiry_date DROP NOT NULL;
            """,
        ),
    ]