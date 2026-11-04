import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_accounts", "0008_socialaccountinvitationacceptanceaccount"),
    ]

    operations = [
        migrations.CreateModel(
            name="SocialAccountInvitationOAuthAttempt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "platform",
                    models.CharField(
                        choices=[("facebook", "Facebook"), ("instagram", "Instagram")],
                        max_length=20,
                    ),
                ),
                ("state_hash", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "acceptance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oauth_attempts",
                        to="social_accounts.socialaccountinvitationacceptance",
                    ),
                ),
            ],
            options={
                "db_table": "social_account_invitation_oauth_attempts",
            },
        ),
        migrations.AddIndex(
            model_name="socialaccountinvitationoauthattempt",
            index=models.Index(
                fields=["acceptance", "platform", "expires_at"],
                name="soc_inv_oauth_acc_plat_exp_idx",
            ),
        ),
    ]
