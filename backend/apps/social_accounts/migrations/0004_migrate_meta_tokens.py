from django.db import migrations


def migrate_meta_tokens(apps, schema_editor):
    SocialConnection = apps.get_model(
        "social_accounts",
        "SocialConnection",
    )

    SocialAccount = apps.get_model(
        "social_accounts",
        "SocialAccount",
    )

    MetaAccountCredential = apps.get_model(
        "meta_integration",
        "MetaAccountCredential",
    )

    from cryptography.fernet import Fernet
    from django.conf import settings

    encryption_key = getattr(
        settings,
        "META_CREDENTIAL_ENCRYPTION_KEY",
        None,
    )

    if not encryption_key:
        raise RuntimeError("META_CREDENTIAL_ENCRYPTION_KEY is not configured.")

    fernet = Fernet(
        encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
    )

    connections = SocialConnection.objects.filter(
        provider="meta",
        is_deleted=False,
    ).exclude(
        access_token="",
    )

    for connection in connections:
        social_accounts = SocialAccount.objects.filter(
            connection_id=connection.id,
            is_deleted=False,
        )

        for social_account in social_accounts:
            existing = MetaAccountCredential.objects.filter(
                social_account_id=social_account.id,
                is_deleted=False,
            ).first()

            if existing:
                continue

            encrypted_token = fernet.encrypt(connection.access_token.encode()).decode()

            MetaAccountCredential.objects.create(
                social_account_id=social_account.id,
                credential_type="user",
                access_token=encrypted_token,
                status="active",
            )


def reverse_migrate_meta_tokens(apps, schema_editor):
    """
    Intentionally do not restore plaintext tokens.

    Rolling back this migration must never copy encrypted
    credentials back into SocialConnection.access_token.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "social_accounts",
            "0003_socialconnection_and_more",
        ),
        (
            "meta_integration",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.RunPython(
            migrate_meta_tokens,
            reverse_migrate_meta_tokens,
        ),
    ]
