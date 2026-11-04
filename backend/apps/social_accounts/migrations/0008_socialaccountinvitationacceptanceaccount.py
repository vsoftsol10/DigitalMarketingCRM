import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_accounts", "0007_socialaccountinvitation_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SocialAccountInvitationAcceptanceAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("platform", models.CharField(choices=[("instagram", "Instagram"), ("facebook", "Facebook"), ("linkedin", "LinkedIn"), ("youtube", "YouTube")], max_length=20)),
                ("platform_account_id", models.CharField(max_length=255)),
                ("acceptance", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="connected_accounts", to="social_accounts.socialaccountinvitationacceptance")),
                ("social_account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="invitation_acceptance_links", to="social_accounts.socialaccount")),
            ],
            options={
                "db_table": "social_account_invitation_acceptance_accounts",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="socialaccountinvitationacceptanceaccount",
            constraint=models.UniqueConstraint(condition=models.Q(("social_account__isnull", False)), fields=("acceptance", "social_account"), name="soc_inv_acc_account_unique"),
        ),
        migrations.AddIndex(
            model_name="socialaccountinvitationacceptanceaccount",
            index=models.Index(fields=["platform", "platform_account_id"], name="soc_inv_acc_account_ext_idx"),
        ),
    ]
