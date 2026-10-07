from django.db import migrations, models


def copy_overall_status_to_content_stage(apps, schema_editor):
    SyncState = apps.get_model("insights", "InsightsSyncState")
    SyncState.objects.all().update(content_status=models.F("status"))


class Migration(migrations.Migration):

    dependencies = [
        ("insights", "0002_insightsaccountsnapshot_profile_metadata_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="insightssyncstate",
            name="content_status",
            field=models.CharField(
                choices=[
                    ("queued", "Queued"),
                    ("syncing", "Syncing"),
                    ("complete", "Complete"),
                    ("partial", "Partial"),
                    ("failed", "Failed"),
                ],
                db_index=True,
                default="queued",
                max_length=16,
            ),
        ),
        migrations.RunPython(
            copy_overall_status_to_content_stage,
            migrations.RunPython.noop,
        ),
    ]
