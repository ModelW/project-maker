from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from rest_framework.routers import DefaultRouter, SimpleRouter

# :: IF api__wagtail
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from ___project_name__snake___.apps.cms.api import cms_api_router

# :: ENDIF
from ___project_name__snake___.apps.people.views import MeViewSet

admin.site.site_title = _("___project_name__natural_double_quoted___")
admin.site.site_header = _("___project_name__natural_double_quoted___")


if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("me", MeViewSet, basename="me")

urlpatterns = [
    path("back/_/ht/", include("___project_name__snake___.apps.health.urls")),
    path("back/admin/", admin.site.urls),
    path("back/api/", include(router.urls)),
    # :: IF api__wagtail
    path("back/___cms_prefix___/", include(wagtailadmin_urls)),
    path("back/api/cms/", cms_api_router.urls),
    path("back/documents/", include(wagtaildocs_urls)),
    path("", include(wagtail_urls)),
    # :: ENDIF
]

if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    urlpatterns = [
        path(
            "back/api/schema/",
            SpectacularAPIView.as_view(),
            name="schema",
        ),
        path(
            "back/api/schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "back/api/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
        path("back/__debug__/", include("debug_toolbar.urls")),
    ] + urlpatterns
