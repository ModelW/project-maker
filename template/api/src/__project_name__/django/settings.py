from model_w.env_manager import EnvManager
from model_w.preset.django import ModelWDjango

with EnvManager(ModelWDjango()) as env:
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]

    ROOT_URLCONF = "demo_django.urls"

    WSGI_APPLICATION = "demo_django.wsgi.application"
    ASGI_APPLICATION = "demo_django.asgi.application"

    LANGUAGES = [
        ("en", "English"),
    ]
