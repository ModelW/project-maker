# :: IF api__celery
from datetime import timedelta

# :: ENDIF
from importlib import metadata

from model_w.env_manager import EnvManager
from model_w.preset.django import ModelWDjango

# Variables set by the EnvManager but declared here so IDEs don't complain
DEBUG = False
MIDDLEWARE = []
REST_FRAMEWORK = {}


def get_package_version() -> str:
    """
    Trying to get the current package version using the metadata module. This
    assumes that the version is indeed set in pyproject.toml and that the
    package was cleanly installed.
    """
    try:
        return metadata.version("___project_name__snake___")
    except metadata.PackageNotFoundError:
        return "0.0.0"


with EnvManager(ModelWDjango()) as env:
    # ---
    # Apps
    # ---

    INSTALLED_APPS = [
        "drf_spectacular",
        "drf_spectacular_sidecar",
        # :: IF api__channels
        "___project_name__snake___.apps.realtime",
        # :: ENDIF
        # :: IF api__wagtail
        "___project_name__snake___.apps.cms",
        # :: ENDIF
        "___project_name__snake___.apps.people",
        "___project_name__snake___.apps.health",
    ]

    # ---
    # Plumbing
    # ---

    ROOT_URLCONF = "___project_name__snake___.django.urls"

    WSGI_APPLICATION = "___project_name__snake___.django.wsgi.application"
    # :: IF api__channels
    ASGI_APPLICATION = "___project_name__snake___.django.asgi.application"
    # :: ENDIF

    # ---
    # Auth
    # ---

    AUTH_USER_MODEL = "people.User"

    # ---
    # i18n
    # ---

    LANGUAGES = [
        ("en", "English"),
    ]

    # ---
    # OpenAPI Schema
    # ---

    REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"

    SPECTACULAR_SETTINGS = {
        "TITLE": "___project_name__natural_double_quoted___",
        "VERSION": get_package_version(),
        "SERVE_INCLUDE_SCHEMA": False,
        "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
        "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
        "REDOC_DIST": "SIDECAR",
    }

    # :: IF api__wagtail
    # ---
    # Wagtail
    # ---

    WAGTAIL_SITE_NAME = "___project_name__natural_double_quoted___"
    WAGTAILIMAGES_IMAGE_MODEL = "cms.CustomImage"
    WAGTAILDOCS_DOCUMENT_MODEL = "cms.CustomDocument"
    # :: ENDIF

    # :: IF api__celery
    # ---
    # Celery tasks to control celery and celery beat health
    # ---
    CELERY_BEAT_SCHEDULE = {
        "log-beat": {
            "task": "___project_name__snake___.apps.health.tasks.log_beat",
            "schedule": timedelta(minutes=1),
        },
        "clean-health-log": {
            "task": "___project_name__snake___.apps.health.tasks.clear_log",
            "schedule": timedelta(hours=1),
        },
        "check-status": {
            "task": "___project_name__snake___.apps.health.tasks.check_status",
            "schedule": timedelta(minutes=1),
        },
    }
    # :: ENDIF

    if DEBUG:
        # Django Debug Toolbar
        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")
        INTERNAL_IPS = [
            "127.0.0.1",
        ]
        DEBUG_TOOLBAR_CONFIG = {
            "SHOW_COLLAPSED": True,
        }

        # Django Extensions
        INSTALLED_APPS.append("django_extensions")
