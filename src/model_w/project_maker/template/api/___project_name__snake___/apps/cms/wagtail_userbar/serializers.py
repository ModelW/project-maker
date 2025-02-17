"""Serializers for the Wagtail userbar API."""

from django.db import models as django_models
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class WagtailUserbarRequestSerializer(serializers.Serializer):
    """
    Serializer for the Wagtail userbar API.
    We accept either a page ID or URL path to get the userbar.
    If both are provided, the page ID takes precedence.

    """

    class Position(django_models.TextChoices):
        TOP_LEFT = "top-left", _("Top left")
        TOP_RIGHT = "top-right", _("Top right")
        BOTTOM_LEFT = "bottom-left", _("Bottom left")
        BOTTOM_RIGHT = "bottom-right", _("Bottom right")

    position = serializers.ChoiceField(
        choices=Position.choices,
        help_text=_("Position of the Wagtail userbar"),
        required=False,
        default=Position.BOTTOM_RIGHT,
        write_only=True,
    )


class WagtailUserbarResponseSerializer(serializers.Serializer):
    """
    The serializer for the Wagtail userbar API response.
    It only contains the HTML content of the userbar to be rendered in the front.
    """

    html = serializers.CharField(
        help_text=_("HTML content of the Wagtail userbar"),
    )
