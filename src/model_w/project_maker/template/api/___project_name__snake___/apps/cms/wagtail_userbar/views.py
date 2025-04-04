"""
The Wagtail userbar API endpoint.

It is a simple ViewSet as we don't need to do anything fancy here.
However, to keep it consistent with the other API endpoints, we provide the
expected elements that the WagtailAPIRouter expects (ie. get_urlpatterns) so
we can register it as an endpoint inside the cms_api_router.
"""

import logging

from django.urls import URLPattern, URLResolver, path
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import permissions, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from wagtail.admin.templatetags.wagtailuserbar import wagtailuserbar
from wagtail.models import Page

from . import serializers

logger = logging.getLogger(__name__)


class WagtailUserbarAPIView(viewsets.ViewSet):
    """
    ViewSet to serve the Wagtail userbar.
    A single list endpoint is provided where the page ID or URL path is provided
    and the userbar HTML content is returned to be rendered in the front.

    We provide the expected elements that the WagtailAPIRouter expects to register
    the endpoint, so we can keep it consistent with the other API endpoints.
    """

    model = Page
    permission_classes = [permissions.IsAuthenticated]

    def get_page(self, pk: int) -> Page | None:
        """Get the page the userbar is for."""
        page = None
        try:
            page = Page.objects.get(pk=pk)
        except Page.DoesNotExist:
            logger.exception("Tried to get userbar for non-existent page: %s", pk)
        return page

    def mark_in_preview_panel(self, request: Request) -> bool:
        """
        Check if the request is in preview panel, and if so mark the expected attribute.
        This is obviously fragile, and so is tested for in ModelW to keep it up to date
        when the Wagtail API changes.
        """
        if in_preview_panel := request.query_params.get("in_preview_panel"):
            request.in_preview_panel = True

        return bool(in_preview_panel)

    @extend_schema(
        request=serializers.WagtailUserbarRequestSerializer,
        responses={200: serializers.WagtailUserbarResponseSerializer},
        examples=[
            OpenApiExample(
                "Wagtail userbar example response.",
                value={
                    "html": '<!-- Wagtail user bar embed code -->\n<template id="wagtail-userbar-template">\n    \n    <aside >\n        <div class="w-userbar w-userbar--bottom-right w-theme-system w-density-default" data-wagtail-userbar part="userbar">\n</div>',
                },
                request_only=False,
                response_only=True,
            ),
        ],
    )
    def detail_view(self, request: Request, pk: int) -> Response:
        """
        Endpoint to serve the Wagtail userbar HTML.
        The pk refers to the page ID that the userbar is for.
        We return the HTML content of the userbar to be rendered in the front.
        """
        html = ""
        page = self.get_page(pk)
        position = request.query_params.get("position", "bottom-right")

        if page:
            self.mark_in_preview_panel(request)
            context = {"request": request, "page": page}
            html = wagtailuserbar(context=context, position=position)

        response_serializer = serializers.WagtailUserbarResponseSerializer(
            data={"html": html},
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data)

    @classmethod
    def get_urlpatterns(cls) -> list[URLPattern | URLResolver]:
        """
        Return the URL patterns for the view.
        Only a detail view is provided, as the Wagtail userbar works on a single page.
        """
        return [
            path("<int:pk>/", cls.as_view({"get": "detail_view"}), name="detail"),
        ]
