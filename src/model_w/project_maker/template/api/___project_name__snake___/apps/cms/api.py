"""
The API endpoint for headless CMS functionality.

As well as the standard Wagtail API endpoints, this module provides am additional
endpoint for grabbing the preview data when in preview mode.
"""

import logging

from django.apps import apps
from django.db import models
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from wagtail.admin.views.generic.preview import Block
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.contrib.redirects.models import Redirect
from wagtail.images.api.v2.views import BaseAPIViewSet

from . import utils
from .wagtail_userbar.views import WagtailUserbarAPIView

logger = logging.getLogger(__name__)


class ApiStreamFieldBlockPreview(utils.ApiStreamFieldBlockPreview):
    """The block preview for the API."""


class PreviewPagesAPIViewSet(PagesAPIViewSet):
    permission_classes = [IsAuthenticated]

    def listing_view(self, request: Request) -> Response:
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


class PreviewSnippetsViewSet(BaseAPIViewSet):
    """
    A specific view set for previewing snippets.
    Similar to the PreviewPagesAPIViewSet, but as snippets are not subclasses of Page,
    we use a different view set to retrieve the model, rather than hacking the page one.
    """

    permission_classes = [IsAuthenticated]
    model = utils.ApiSnippet

    def get_object(self) -> utils.ApiSnippet:
        """Get the preview data for snippets stored in the session."""
        logger.debug("Getting object being previewed...")
        model, data = utils.PreviewDataStore.get_preview_data(self.request)

        snippet_model = apps.get_model(model)
        instance = snippet_model.from_json(data)
        instance.pk = 0

        logger.debug("Got object: %s", instance)
        return instance

    def get_queryset(self) -> models.QuerySet:
        """Return the snippets for the current user."""
        return self.get_snippet_model().objects.all()

    def get_snippet_model(self) -> models.Model:
        """Retrieve the snippet model based on the model identifier."""
        return apps.get_model(self.get_snippet_type())

    def get_snippet_type(self) -> str:
        """Return the name of the snippet model from the request kwargs."""
        return self.request.query_params.get("type", "")

    def listing_view(self, request: Request) -> Response:
        """
        As we don't have a concept of 'many' preview data, we route all requests
        to the detail view with a dummy pk.

        """
        self.action = "detail_view"
        return self.detail_view(request, pk=0)


class PreviewBlocksViewSet(BaseAPIViewSet):
    """
    ViewSet for previewing blocks.
    Similar to the PreviewPagesAPIViewSet, but as blocks are not DB models themselves,
    we treat them slightly differently.  Also, as the preview value is hard-coded, we
    need not use the session for storage/retrieval.
    """

    permission_classes = [IsAuthenticated]
    model = Block

    def listing_view(self, request: Request) -> Response:
        """
        To keep the logic consistent with the page & snippet preview, we receive the app
        dot model and block ID as query params, and passed to the detail view to retrieve
        the block preview data.
        """
        pk = self.request.query_params.get("id")
        app_dot_model = self.request.query_params.get("in_preview_panel")
        logger.debug(
            "Getting detail view for block with PK %s in %s",
            pk,
            app_dot_model,
        )
        return self.detail_view(request, pk=pk, app_dot_model=app_dot_model)

    def detail_view(self, request: Request, pk: str, app_dot_model: str):
        """Get the block preview data from the block ID."""
        logger.debug("Getting object for block %s", pk)
        block = self.get_object(pk)
        block["meta"] = {
            "type": app_dot_model,
        }
        logger.debug("Returning block %s", block)
        return Response(block)

    def get_object(self, block_id: str) -> dict:
        """Get the preview data for the block."""
        return self.block_def(block_id).get_api_representation(
            value=self.block_def(block_id).get_preview_value(),
            context={"request": self.request},
        )

    def block_def(self, block_id: str) -> Block:
        """
        Retrieve the block definition for the preview.
        Mimic what happens in block_def in StreamFieldBlockPreview.
        """
        if not (block := Block.definition_registry.get(block_id)):
            raise Http404
        return block


class CustomPagesAPIViewSet(PagesAPIViewSet):
    permission_classes = [AllowAny]

    def find_view(self, request: Request):
        """
        When getting pages via the `html_path` query param, if not found, a 404 is returned,
        without checking if a redirect exists.  Furthermore, it's hard to break out of the
        WagtailAPIRouter with standard redirect & Location header, as it tries to get a template.
        Therefore, we add a custom redirect header to the response, and let the client handle it.
        """
        try:
            return super().find_view(request)
        except Http404:
            logger.debug("No CMS page found, looking for a redirect rule...")
            try:
                if html_path_param := request.query_params.get("html_path"):
                    html_path = Redirect.normalise_path(html_path_param)

                redirect = Redirect.objects.get(old_path=html_path)
                headers = {
                    "X-Redirect-To": redirect.link,
                }
                return Response(
                    status=(
                        status.HTTP_301_MOVED_PERMANENTLY
                        if redirect.is_permanent
                        else status.HTTP_302_FOUND
                    ),
                    headers=headers,
                )
            except Redirect.DoesNotExist:
                logger.debug("No redirect found, returning 404")
                raise Http404 from None


cms_api_router = WagtailAPIRouter("wagtailapi")

cms_api_router.register_endpoint("pages", CustomPagesAPIViewSet)
cms_api_router.register_endpoint("preview", PreviewPagesAPIViewSet)
cms_api_router.register_endpoint("preview-snippet", PreviewSnippetsViewSet)
cms_api_router.register_endpoint("preview-block", PreviewBlocksViewSet)
cms_api_router.register_endpoint("wagtail-userbar", WagtailUserbarAPIView)
