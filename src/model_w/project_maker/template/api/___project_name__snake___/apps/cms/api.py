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
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.contrib.redirects.models import Redirect
from wagtail.images.api.v2.views import BaseAPIViewSet

from . import utils

logger = logging.getLogger(__name__)


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
                    status=status.HTTP_301_MOVED_PERMANENTLY
                    if redirect.is_permanent
                    else status.HTTP_302_FOUND,
                    headers=headers,
                )
            except Redirect.DoesNotExist:
                logger.debug("No redirect found, returning 404")
                raise Http404 from None


cms_api_router = WagtailAPIRouter("wagtailapi")

cms_api_router.register_endpoint("pages", CustomPagesAPIViewSet)
cms_api_router.register_endpoint("preview", PreviewPagesAPIViewSet)
cms_api_router.register_endpoint("preview-snippet", PreviewSnippetsViewSet)
