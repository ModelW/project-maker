from importlib import metadata

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from ninja import NinjaAPI

# :: IF api__wagtail
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from ___project_name__snake___.apps.cms.api import (
    cms_api_router,
    ApiStreamFieldBlockPreview,
)
# :: ENDIF
from ___project_name__snake___.apps.people.api import router as people_router

admin.site.site_title = _("___project_name__natural_double_quoted___")
admin.site.site_header = _("___project_name__natural_double_quoted___")

api = NinjaAPI(
    title="___project_name__natural___ API",
    version=metadata.version("~~~project_name__snake~~~"),
    docs_url=(settings.DEBUG and "/docs") or "",
    openapi_url=(settings.DEBUG and "/openapi.json") or "",
)

api.add_router("/me", people_router)

urlpatterns = [
    path("back/_/ht/", include("___project_name__snake___.apps.health.urls")),
    path("back/admin/", admin.site.urls),
    path("back/api/", api.urls),
    # :: IF api__wagtail
    path(
        "back/___cms_prefix___/block-preview/",
        ApiStreamFieldBlockPreview.as_view(),
        name="wagtailadmin_block_preview",
    ),
    path("back/___cms_prefix___/", include(wagtailadmin_urls)),
    path("back/api/cms/", cms_api_router.urls),
    path("back/documents/", include(wagtaildocs_urls)),
    path("", include(wagtail_urls)),
    # :: ENDIF
]

if settings.DEBUG:
    urlpatterns += [
        path("back/__debug__/", include("debug_toolbar.urls")),
    ]
