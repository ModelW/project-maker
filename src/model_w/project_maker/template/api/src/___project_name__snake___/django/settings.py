from importlib import metadata

from model_w.env_manager import EnvManager
from model_w.preset.django import ModelWDjango

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
        "___project_name__snake___.core",
        "___project_name__snake___.people",
        # :: IF api__wagtail
        "___project_name__snake___.cms",
        # :: ENDIF
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
