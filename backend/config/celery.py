import os

from celery import Celery

from .celery_diagnostics import connect_task_diagnostics

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


app = Celery(
    "digital_marketing_platform",
)


app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)


app.autodiscover_tasks()

connect_task_diagnostics()
