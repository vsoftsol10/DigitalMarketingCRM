from django.db import migrations, models


def copy_legacy_pending_hashes(apps, schema_editor):
    Invitation = apps.get_model("social_accounts", "SocialAccountInvitation")
    Invitation.objects.filter(
        delivery_status="pending",
        pending_token_hash="",
    ).update(pending_token_hash=models.F("token_hash"))


class Migration(migrations.Migration):

    dependencies = [
        ("social_accounts", "0009_socialaccountinvitationoauthattempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="socialaccountinvitation",
            name="pending_token_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.RunPython(copy_legacy_pending_hashes, migrations.RunPython.noop),
    ]
