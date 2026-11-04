import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram_integration", "0001_initial"),
        ("social_accounts", "0009_socialaccountinvitationoauthattempt"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvitationInstagramOAuthSession",
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
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                ("instagram_user_id", models.CharField(max_length=255)),
                ("username", models.CharField(blank=True, max_length=255)),
                ("account_name", models.CharField(blank=True, max_length=255)),
                ("profile_image", models.URLField(blank=True, max_length=2048)),
                ("encrypted_access_token", models.TextField()),
                ("token_expires_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("staged", "Staged"),
                            ("confirmed", "Confirmed"),
                            ("declined", "Declined"),
                            ("invalidated", "Invalidated"),
                            ("expired", "Expired"),
                        ],
                        db_index=True,
                        default="staged",
                        max_length=20,
                    ),
                ),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("declined_at", models.DateTimeField(blank=True, null=True)),
                ("invalidated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "acceptance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="instagram_oauth_sessions",
                        to="social_accounts.socialaccountinvitationacceptance",
                    ),
                ),
                (
                    "oauth_attempt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="instagram_staging_session",
                        to="social_accounts.socialaccountinvitationoauthattempt",
                    ),
                ),
            ],
            options={"db_table": "invitation_instagram_oauth_sessions"},
        ),
        migrations.AddIndex(
            model_name="invitationinstagramoauthsession",
            index=models.Index(
                fields=["acceptance", "status", "expires_at"],
                name="inv_ig_oauth_acc_state_exp_idx",
            ),
        ),
    ]
