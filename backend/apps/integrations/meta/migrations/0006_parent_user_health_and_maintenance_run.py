from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("meta_integration", "0005_alter_metaaccountcredential_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="metaaccountcredential",
            name="provider_token_type",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="metaaccountcredential",
            name="provider_is_valid",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metaaccountcredential",
            name="provider_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metaaccountcredential",
            name="data_access_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metaaccountcredential",
            name="last_health_check_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metaaccountcredential",
            name="granted_permissions",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="MetaTokenMaintenanceRun",
            fields=[
                (
                    "run_id",
                    models.UUIDField(primary_key=True, serialize=False, editable=False),
                ),
                ("started_at", models.DateTimeField()),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("duration_ms", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("RUNNING", "Running"),
                            ("SUCCESS", "Success"),
                            ("PARTIAL", "Partial"),
                            ("FAILED", "Failed"),
                        ],
                        max_length=10,
                    ),
                ),
                ("checked", models.PositiveIntegerField(default=0)),
                ("valid", models.PositiveIntegerField(default=0)),
                ("invalid", models.PositiveIntegerField(default=0)),
                ("retry", models.PositiveIntegerField(default=0)),
                ("reconnect_needed", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "meta_token_maintenance_runs",
                "ordering": ["-started_at"],
            },
        ),
    ]
