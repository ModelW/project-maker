"""
The API endpoint for headless CMS functionality.

As well as the standard Wagtail API endpoints, this module provides am additional
endpoint for grabbing the preview data when in preview mode.
"""

import logging

from django.apps import apps
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import HttpRequest
from rest_framework.response import Response
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet

from . import utils

logger = logging.getLogger(__name__)


class PreviewPagesAPIViewSet(PagesAPIViewSet):
    permission_classes = [IsAuthenticated]

    def listing_view(self, request: HttpRequest) -> Response:
        """
        As we don't have a concept of 'many' preview data, we route all requests
        to the detail view with a dummy pk.

        Note: To get the correct serializer, we need to change the action.
        """
        self.action = "detail_view"
        return super().detail_view(request, pk=0)

    def get_object(self) -> utils.ApiPage:
        """Get the preview data which is stored in the session."""
        logger.debug("Getting object being previewed...")
        model, data = utils.PreviewDataStore.get_preview_data(self.request)

        page_model = apps.get_model(model)
        instance = page_model.from_json(data)
        instance.pk = 0

        logger.debug("Got object: %s", instance)
        return instance


class CustomPagesAPIViewSet(PagesAPIViewSet):
    permission_classes = [AllowAny]


class CustomImagesAPIViewSet(ImagesAPIViewSet):
    permission_classes = [AllowAny]


class CustomDocumentsAPIViewSet(DocumentsAPIViewSet):
    permission_classes = [AllowAny]


cms_api_router = WagtailAPIRouter("wagtailapi")

cms_api_router.register_endpoint("pages", CustomPagesAPIViewSet)
cms_api_router.register_endpoint("images", CustomImagesAPIViewSet)
cms_api_router.register_endpoint("documents", CustomDocumentsAPIViewSet)
cms_api_router.register_endpoint("preview", PreviewPagesAPIViewSet)
