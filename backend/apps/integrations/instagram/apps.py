from django.apps import AppConfig


class InstagramIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations.instagram"
    label = "instagram_integration"
    verbose_name = "Instagram Integration"