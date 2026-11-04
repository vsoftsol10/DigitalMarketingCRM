import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("meta_integration", "0006_parent_user_health_and_maintenance_run"),
        ("social_accounts", "0009_socialaccountinvitationoauthattempt"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvitationMetaOAuthSession",
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
                    "selection_key",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
                ),
                ("provider_user_id", models.CharField(max_length=255)),
                ("encrypted_access_token", models.TextField()),
                ("encrypted_accounts", models.TextField()),
                ("token_expires_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "acceptance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="meta_oauth_sessions",
                        to="social_accounts.socialaccountinvitationacceptance",
                    ),
                ),
                (
                    "oauth_attempt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="meta_selection_session",
                        to="social_accounts.socialaccountinvitationoauthattempt",
                    ),
                ),
            ],
            options={
                "db_table": "invitation_meta_oauth_sessions",
            },
        ),
        migrations.AddIndex(
            model_name="invitationmetaoauthsession",
            index=models.Index(
                fields=["acceptance", "expires_at"],
                name="inv_meta_oauth_acc_exp_idx",
            ),
        ),
    ]
