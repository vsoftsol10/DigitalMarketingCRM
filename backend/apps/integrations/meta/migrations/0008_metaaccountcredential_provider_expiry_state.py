from django.db import migrations, models


def classify_existing_user_expiry_state(apps, schema_editor):
    MetaAccountCredential = apps.get_model(
        "meta_integration",
        "MetaAccountCredential",
    )
    database = schema_editor.connection.alias
    credentials = MetaAccountCredential.objects.using(database)

    credentials.filter(
        credential_type="user",
        provider_expires_at__isnull=False,
    ).update(provider_expiry_state="FINITE")
    credentials.filter(
        credential_type="user",
        provider_expires_at__isnull=True,
    ).update(provider_expiry_state="UNKNOWN")
    credentials.filter(credential_type="page").update(
        provider_expiry_state=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("meta_integration", "0007_invitationmetaoauthsession"),
    ]

    operations = [
        migrations.AddField(
            model_name="metaaccountcredential",
            name="provider_expiry_state",
            field=models.CharField(
                blank=True,
                choices=[
                    ("UNKNOWN", "Unknown"),
                    ("FINITE", "Finite"),
                    ("NO_FINITE_EXPIRY", "No finite expiry"),
                ],
                default=None,
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(
            classify_existing_user_expiry_state,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="metaaccountcredential",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        credential_type="user",
                        provider_expiry_state__in=[
                            "UNKNOWN",
                            "FINITE",
                            "NO_FINITE_EXPIRY",
                        ],
                    )
                    | models.Q(
                        credential_type="page",
                        provider_expiry_state__isnull=True,
                    )
                ),
                name="meta_cred_exp_state_owner",
            ),
        ),
    ]
