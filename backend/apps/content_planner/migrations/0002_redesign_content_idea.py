from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("content_planner", "0001_initial"),
        ("social_accounts", "0005_remove_socialconnection_access_token"),
    ]

    operations = [
        migrations.RenameField(
            model_name="contentidea",
            old_name="title",
            new_name="caption",
        ),
        migrations.AlterField(
            model_name="contentidea",
            name="caption",
            field=models.CharField(max_length=2200),
        ),
        migrations.AlterField(
            model_name="contentidea",
            name="content_type",
            field=models.CharField(
                choices=[("POST", "Post"), ("REEL", "Reel"), ("STORY", "Story")],
                db_index=True,
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="contentidea",
            name="platform",
            field=models.CharField(
                blank=True,
                choices=[("INSTAGRAM", "Instagram"), ("FACEBOOK", "Facebook"), ("YOUTUBE", "YouTube"), ("LINKEDIN", "LinkedIn"), ("X", "X (Twitter)")],
                db_index=True,
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="contentidea",
            name="campaign_goal",
            field=models.CharField(blank=True, db_index=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name="contentidea",
            name="target_publish_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contentidea",
            name="selected_social_accounts",
            field=models.ManyToManyField(blank=True, related_name="content_ideas", to="social_accounts.socialaccount"),
        ),
    ]
