import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "___project_name__snake___.django.settings"
)

app = Celery("___project_name__dashed___")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
